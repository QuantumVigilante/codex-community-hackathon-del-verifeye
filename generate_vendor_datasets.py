import json
import random
import uuid
from datetime import datetime, timedelta


random.seed(42)


GST_ALPHANUM = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def generate_gstin(state_code):
    pan_letters = "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(5))
    pan_digits = "".join(str(random.randint(0, 9)) for _ in range(4))
    pan_last = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    entity_code = random.choice("123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    checksum = random.choice(GST_ALPHANUM)
    return f"{state_code:02d}{pan_letters}{pan_digits}{pan_last}{entity_code}Z{checksum}"


def round_inr(value):
    return round(value + 1e-9, 2)


def calculate_tax(amount, tax_rate):
    return round_inr(amount * tax_rate)


def calculate_invoice_total(line_items):
    total = 0.0
    for item in line_items:
        subtotal = item["hours"] * item["billed_rate"]
        total += subtotal + item["tax_charged"]
    return round_inr(total)


def build_line_item(description, hours, billed_rate, tax_rate):
    subtotal = round_inr(hours * billed_rate)
    tax_charged = calculate_tax(subtotal, tax_rate)
    return {
        "description": description,
        "hours": hours,
        "billed_rate": billed_rate,
        "tax_charged": tax_charged,
    }


def generate_contracts():
    vendor_specs = [
        {
            "vendor_name": "Apex IT Solutions",
            "state_code": 27,
            "approved_rates": {
                "Cloud Consulting": 4200,
                "Server Maintenance": 2500,
                "Cybersecurity Audit": 5200,
            },
            "travel_expense_cap": 18000,
        },
        {
            "vendor_name": "Vanguard Logistics",
            "state_code": 29,
            "approved_rates": {
                "Fleet Optimization": 3100,
                "Warehouse Systems Support": 2800,
                "Supply Chain Analytics": 3600,
            },
            "travel_expense_cap": 22000,
        },
        {
            "vendor_name": "Nimbus Data Systems",
            "state_code": 7,
            "approved_rates": {
                "Data Engineering": 4800,
                "ETL Monitoring": 3400,
                "Platform Reliability": 3900,
            },
            "travel_expense_cap": 15000,
        },
    ]

    contracts = []
    for spec in vendor_specs:
        contracts.append(
            {
                "contract_id": str(uuid.uuid4()),
                "vendor_name": spec["vendor_name"],
                "gstin": generate_gstin(spec["state_code"]),
                "approved_rates": spec["approved_rates"],
                "travel_expense_cap": spec["travel_expense_cap"],
                "standard_tax_slab": 0.18,
            }
        )
    return contracts


def generate_invoices(contracts):
    contract_by_vendor = {contract["vendor_name"]: contract for contract in contracts}
    base_date = datetime(2026, 4, 18)

    apex = contract_by_vendor["Apex IT Solutions"]
    vanguard = contract_by_vendor["Vanguard Logistics"]
    nimbus = contract_by_vendor["Nimbus Data Systems"]

    invoice_1_items = [
        build_line_item("Cloud Consulting", 12, apex["approved_rates"]["Cloud Consulting"], 0.18),
        build_line_item("Server Maintenance", 8, apex["approved_rates"]["Server Maintenance"], 0.18),
    ]

    invoice_2_items = [
        build_line_item(
            "Warehouse Systems Support",
            14,
            vanguard["approved_rates"]["Warehouse Systems Support"],
            0.18,
        ),
        build_line_item(
            "Supply Chain Analytics",
            9,
            vanguard["approved_rates"]["Supply Chain Analytics"],
            0.18,
        ),
    ]

    invoice_3_items = [
        build_line_item("Data Engineering", 11, nimbus["approved_rates"]["Data Engineering"], 0.24),
        build_line_item("ETL Monitoring", 7, nimbus["approved_rates"]["ETL Monitoring"], 0.24),
    ]

    inflated_rate = vanguard["approved_rates"]["Fleet Optimization"] + 800
    invoice_4_items = [
        build_line_item("Fleet Optimization", 10, inflated_rate, 0.18),
        build_line_item(
            "Warehouse Systems Support",
            6,
            vanguard["approved_rates"]["Warehouse Systems Support"],
            0.18,
        ),
    ]

    excessive_travel_expense = apex["travel_expense_cap"] + 6500
    invoice_5_items = [
        build_line_item(
            "Cybersecurity Audit",
            5,
            apex["approved_rates"]["Cybersecurity Audit"],
            0.18,
        ),
        build_line_item("Travel Expenses", 1, excessive_travel_expense, 0.18),
    ]

    raw_invoices = [
        ("INV-2026-001", apex["vendor_name"], base_date - timedelta(days=20), invoice_1_items),
        ("INV-2026-002", vanguard["vendor_name"], base_date - timedelta(days=15), invoice_2_items),
        ("INV-2026-003", nimbus["vendor_name"], base_date - timedelta(days=10), invoice_3_items),
        ("INV-2026-004", vanguard["vendor_name"], base_date - timedelta(days=6), invoice_4_items),
        ("INV-2026-005", apex["vendor_name"], base_date - timedelta(days=2), invoice_5_items),
    ]

    invoices = []
    for invoice_id, vendor_name, invoice_date, line_items in raw_invoices:
        invoices.append(
            {
                "invoice_id": invoice_id,
                "vendor_name": vendor_name,
                "date": invoice_date.date().isoformat(),
                "line_items": line_items,
                "total_billed_amount": calculate_invoice_total(line_items),
            }
        )
    return invoices


def write_json_file(file_path, payload):
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=4)
    except OSError as exc:
        raise RuntimeError(f"Failed to write {file_path}: {exc}") from exc


def main():
    contracts = generate_contracts()
    invoices = generate_invoices(contracts)

    write_json_file("contracts.json", contracts)
    write_json_file("invoices.json", invoices)


if __name__ == "__main__":
    main()
