import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from skills import calculate_tax_variance, verify_gstin


SYSTEM_PROMPT = (
    "You are Verifeye, an autonomous Forensic Audit Agent. "
    "Cross-reference the provided Invoice against the Contract. "
    "Flag any financial leakage, overcharges, or tax errors. "
    "You must output strictly in JSON format."
)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "verify_gstin",
            "description": "Verify whether a GSTIN is active or suspended.",
            "parameters": {
                "type": "object",
                "properties": {
                    "gstin": {
                        "type": "string",
                        "description": "The 15-character Indian GSTIN to verify.",
                    }
                },
                "required": ["gstin"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_tax_variance",
            "description": (
                "Calculate the variance between billed tax and expected tax "
                "using the contract tax rate and taxable base amount."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "billed_tax": {
                        "type": "number",
                        "description": "The actual tax billed on the invoice line item.",
                    },
                    "standard_rate": {
                        "type": "number",
                        "description": "The standard contract tax rate, such as 0.18.",
                    },
                    "base_amount": {
                        "type": "number",
                        "description": "The taxable base amount before tax.",
                    },
                },
                "required": ["billed_tax", "standard_rate", "base_amount"],
                "additionalProperties": False,
            },
        },
    },
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    status = result.get("status", "Fail")
    flags = result.get("flags", [])
    recovery_action = result.get("recovery_action", "Review invoice manually.")

    if status not in {"Pass", "Fail"}:
        status = "Fail"
    if not isinstance(flags, list):
        flags = [str(flags)]
    flags = [str(flag) for flag in flags]
    if not isinstance(recovery_action, str):
        recovery_action = str(recovery_action)

    return {
        "status": status,
        "flags": flags,
        "recovery_action": recovery_action,
    }


def _build_fallback_audit(invoice_data: Dict[str, Any], contract_data: Dict[str, Any]) -> Dict[str, Any]:
    flags: List[str] = []
    total_expected = 0.0
    total_actual = _safe_float(invoice_data.get("total_billed_amount"))
    approved_rates = contract_data.get("approved_rates", {})
    standard_tax = _safe_float(contract_data.get("standard_tax_slab"), 0.18)
    travel_cap = _safe_float(contract_data.get("travel_expense_cap"))

    gst_result = verify_gstin(str(contract_data.get("gstin", "")))
    if gst_result.get("status") != "Active":
        flags.append(f"Vendor GSTIN issue: {gst_result.get('message', 'Unknown GSTIN error.')}")

    for item in invoice_data.get("line_items", []):
        description = str(item.get("description", "Unknown Service"))
        hours = _safe_float(item.get("hours"))
        billed_rate = _safe_float(item.get("billed_rate"))
        billed_tax = _safe_float(item.get("tax_charged"))
        base_amount = round(hours * billed_rate, 2)
        total_expected += base_amount + billed_tax

        if description == "Travel Expenses":
            if billed_rate > travel_cap:
                excess = round(billed_rate - travel_cap, 2)
                flags.append(
                    f"Travel expenses exceed contract cap by INR {excess:.2f}."
                )
        else:
            approved_rate = approved_rates.get(description)
            if approved_rate is None:
                flags.append(f"Service '{description}' is not approved in the contract.")
            elif billed_rate > _safe_float(approved_rate):
                overcharge = round(billed_rate - _safe_float(approved_rate), 2)
                flags.append(
                    f"Rate overcharge detected for {description}: INR {overcharge:.2f} per hour above contract."
                )

        tax_variance = calculate_tax_variance(billed_tax, standard_tax, base_amount)
        if abs(tax_variance) > 0.01:
            direction = "higher" if tax_variance > 0 else "lower"
            flags.append(
                f"Tax mismatch on {description}: billed tax is INR {abs(tax_variance):.2f} {direction} than contract tax."
            )

    if round(total_expected, 2) != round(total_actual, 2):
        delta = round(total_actual - total_expected, 2)
        flags.append(
            f"Invoice total mismatch detected: variance of INR {delta:.2f} against line item math."
        )

    if flags:
        return {
            "status": "Fail",
            "flags": flags,
            "recovery_action": "Hold payment, investigate flagged items, and reclaim any excess amount.",
        }

    return {
        "status": "Pass",
        "flags": [],
        "recovery_action": "No action required. Invoice is compliant.",
    }


def _execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    if tool_name == "verify_gstin":
        if "gstin" not in arguments:
            raise ValueError("Missing required argument 'gstin' for verify_gstin.")
        result = verify_gstin(str(arguments["gstin"]))
        return _json_dumps(result)

    if tool_name == "calculate_tax_variance":
        required = ("billed_tax", "standard_rate", "base_amount")
        missing = [name for name in required if name not in arguments]
        if missing:
            raise ValueError(
                "Missing required arguments for calculate_tax_variance: "
                + ", ".join(missing)
            )
        result = calculate_tax_variance(
            billed_tax=_safe_float(arguments["billed_tax"]),
            standard_rate=_safe_float(arguments["standard_rate"]),
            base_amount=_safe_float(arguments["base_amount"]),
        )
        return _json_dumps({"variance": result})

    raise ValueError(f"Unsupported tool requested: {tool_name}")


def audit_invoice(invoice_data: dict, contract_data: dict) -> dict:
    try:
        if not isinstance(invoice_data, dict):
            raise TypeError("invoice_data must be a dictionary.")
        if not isinstance(contract_data, dict):
            raise TypeError("contract_data must be a dictionary.")

        client = OpenAI()
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _json_dumps(
                    {
                        "invoice_data": invoice_data,
                        "contract_data": contract_data,
                        "instructions": {
                            "required_output_schema": {
                                "status": "Pass or Fail",
                                "flags": ["List specific invoice or contract issues"],
                                "recovery_action": "Single remediation string for CFO",
                            }
                        },
                    }
                ),
            },
        ]

        max_iterations = 8
        for _ in range(max_iterations):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                response_format={"type": "json_object"},
            )

            assistant_message = response.choices[0].message
            assistant_payload: Dict[str, Any] = {"role": "assistant", "content": assistant_message.content or ""}

            if assistant_message.tool_calls:
                assistant_payload["tool_calls"] = []
                for tool_call in assistant_message.tool_calls:
                    assistant_payload["tool_calls"].append(
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                    )
                messages.append(assistant_payload)

                for tool_call in assistant_message.tool_calls:
                    try:
                        parsed_args = json.loads(tool_call.function.arguments or "{}")
                        if not isinstance(parsed_args, dict):
                            raise ValueError("Tool arguments must decode to a JSON object.")
                        tool_result = _execute_tool(tool_call.function.name, parsed_args)
                    except Exception as tool_error:
                        tool_result = _json_dumps({"error": str(tool_error)})

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result,
                        }
                    )
                continue

            if not assistant_message.content:
                raise ValueError("Model returned an empty response without tool calls.")

            parsed = json.loads(assistant_message.content)
            if not isinstance(parsed, dict):
                raise ValueError("Model response must be a JSON object.")
            return _normalize_result(parsed)

        raise RuntimeError("Maximum tool-calling iterations reached without a final JSON response.")
    except Exception:
        if not isinstance(invoice_data, dict) or not isinstance(contract_data, dict):
            return {
                "status": "Fail",
                "flags": ["Invalid invoice or contract payload supplied to audit_invoice."],
                "recovery_action": "Validate the input data structure and rerun the audit.",
            }
        return _normalize_result(_build_fallback_audit(invoice_data, contract_data))


def draft_remediation_email(invoice_data: dict, contract_data: dict, audit_results: dict) -> str:
    try:
        if not isinstance(invoice_data, dict):
            raise TypeError("invoice_data must be a dictionary.")
        if not isinstance(contract_data, dict):
            raise TypeError("contract_data must be a dictionary.")
        if not isinstance(audit_results, dict):
            raise TypeError("audit_results must be a dictionary.")

        vendor_name = str(contract_data.get("vendor_name") or invoice_data.get("vendor_name") or "Vendor")
        invoice_id = str(invoice_data.get("invoice_id") or "Unknown Invoice")
        normalized_audit = _normalize_result(audit_results)

        client = OpenAI()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Verifeye's corporate remediation drafting assistant. "
                        "Write a highly professional, firm, and strictly objective email to the vendor. "
                        "Address the vendor by vendor_name. "
                        "Cite the specific invoice_id. "
                        "Explicitly mention the exact audit flags provided. "
                        "State the recovery_action clearly, including the demand for a corrected or revised invoice where applicable. "
                        "Keep the tone firm, corporate, and strictly objective."
                    ),
                },
                {
                    "role": "user",
                    "content": _json_dumps(
                        {
                            "vendor_name": vendor_name,
                            "invoice_id": invoice_id,
                            "invoice_data": invoice_data,
                            "contract_data": contract_data,
                            "audit_results": normalized_audit,
                        }
                    ),
                },
            ],
        )

        email_content = (response.choices[0].message.content or "").strip()
        if not email_content:
            raise ValueError("Empty remediation email received from model.")
        return email_content
    except Exception:
        vendor_name = str(contract_data.get("vendor_name") or invoice_data.get("vendor_name") or "Vendor")
        invoice_id = str(invoice_data.get("invoice_id") or "Unknown Invoice")
        normalized_audit = _normalize_result(audit_results if isinstance(audit_results, dict) else {})
        flags = normalized_audit.get("flags", [])
        recovery_action = normalized_audit.get("recovery_action", "Please provide a corrected invoice.")
        flag_lines = "\n".join(f"- {flag}" for flag in flags) if flags else "- Audit exceptions were identified and require correction."

        return (
            f"Subject: Remediation Required for Invoice {invoice_id}\n\n"
            f"Dear {vendor_name},\n\n"
            f"Our audit review of invoice {invoice_id} identified the following exceptions:\n"
            f"{flag_lines}\n\n"
            f"Required action:\n"
            f"{recovery_action}\n\n"
            f"Please issue a revised invoice reflecting the correct contractual and financial position at the earliest opportunity. "
            f"Payment processing will remain on hold until the discrepancies are resolved.\n\n"
            f"Regards,\n"
            f"Verifeye Audit Desk"
        )


def _load_json_file(file_path: str) -> Any:
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"File not found: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in file: {file_path}") from exc
    except OSError as exc:
        raise OSError(f"Unable to read file: {file_path}") from exc


def _find_contract_for_invoice(
    invoice: Dict[str, Any], contracts: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    vendor_name = invoice.get("vendor_name")
    for contract in contracts:
        if contract.get("vendor_name") == vendor_name:
            return contract
    return None


def main() -> None:
    try:
        invoices = _load_json_file("invoices.json")
        contracts = _load_json_file("contracts.json")

        if not isinstance(invoices, list):
            raise TypeError("invoices.json must contain a list of invoices.")
        if not isinstance(contracts, list):
            raise TypeError("contracts.json must contain a list of contracts.")

        audit_results = []
        for invoice in invoices:
            if not isinstance(invoice, dict):
                audit_results.append(
                    {
                        "invoice_id": None,
                        "audit_result": {
                            "status": "Fail",
                            "flags": ["Invalid invoice record format."],
                            "recovery_action": "Review source data and regenerate the invoice payload.",
                        },
                    }
                )
                continue

            contract = _find_contract_for_invoice(invoice, contracts)
            if contract is None:
                audit_results.append(
                    {
                        "invoice_id": invoice.get("invoice_id"),
                        "audit_result": {
                            "status": "Fail",
                            "flags": ["No matching contract found for invoice vendor."],
                            "recovery_action": "Obtain the correct contract before approving payment.",
                        },
                    }
                )
                continue

            audit_results.append(
                {
                    "invoice_id": invoice.get("invoice_id"),
                    "audit_result": audit_invoice(invoice, contract),
                }
            )

        print(json.dumps(audit_results, indent=4, ensure_ascii=False))
    except Exception as exc:
        error_output = {
            "status": "Fail",
            "flags": [f"Fatal runtime error: {exc}"],
            "recovery_action": "Fix the application error and rerun the auditor.",
        }
        print(json.dumps(error_output, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
