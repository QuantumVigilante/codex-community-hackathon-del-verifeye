from typing import Dict

def verify_gstin(gstin: str) -> Dict[str, str]:
    """
    Verify the simulated status of an Indian GSTIN.
    This function is designed to act as a lightweight external tool that an
    LLM agent can call to validate the status of a GSTIN (Goods and Services
    Tax Identification Number). It simulates a response from the Indian GST
    portal without making any real network request.

    Behavior:
    - If the provided GSTIN starts with the string "99", the GSTIN is treated
      as suspended or invalid.
    - For all other GSTIN values, the GSTIN is treated as active and valid.

    Args:
        gstin: The GSTIN string to verify. This should be provided exactly as
            received from the upstream workflow or user input.

    Returns:
        A dictionary containing:
        - "status": A short machine-readable result, either "Suspended" or
          "Active".
        - "message": A human-readable explanation of the verification result.
    """
    if gstin.startswith("99"):
        return {
            "status": "Suspended",
            "message": "GSTIN is suspended or invalid.",
        }

    return {
        "status": "Active",
        "message": "GSTIN is valid and active.",
    }

def calculate_tax_variance(
    billed_tax: float, standard_rate: float, base_amount: float
) -> float:
    """
    Calculate the tax variance between billed tax and expected tax.
    This function is intended for agentic audit workflows where an LLM needs a
    reliable arithmetic tool to determine whether a billed tax amount is above
    or below the expected amount derived from the standard contract tax rate.

    The expected tax is calculated as:
        expected_tax = base_amount * standard_rate

    The returned variance is:
        billed_tax - expected_tax

    Interpretation:
    - A positive result means the billed tax is higher than expected
      (overcharged).
    - A negative result means the billed tax is lower than expected
      (undercharged).
    - A zero result means the billed tax matches the expected tax.

    Args:
        billed_tax: The actual tax amount billed on the invoice, in INR.
        standard_rate: The applicable tax rate as a decimal value. For example,
            use 0.18 for 18%.
        base_amount: The taxable base amount on which the standard tax rate
            should be applied, in INR.

    Returns:
        The variance amount in INR, rounded to 2 decimal places.
    """
    expected_tax: float = base_amount * standard_rate
    return round(billed_tax - expected_tax, 2)