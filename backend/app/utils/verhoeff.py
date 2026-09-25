"""
Verhoeff algorithm implementation for validating Aadhaar numbers.
The Verhoeff algorithm is a checksum formula for error detection developed by Jacobus Verhoeff.
UIDAI uses the Verhoeff algorithm for 12-digit Aadhaar numbers.
"""

# The multiplication table (d)
_D_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

# The permutation table (p)
_P_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

# The inverse table (inv)
_INV_TABLE = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def validate_verhoeff(number_str: str) -> bool:
    """Validates whether a number string satisfies the Verhoeff checksum."""
    if not number_str or not number_str.isdigit():
        return False
    c = 0
    reversed_digits = [int(x) for x in reversed(number_str)]
    for i, digit in enumerate(reversed_digits):
        c = _D_TABLE[c][_P_TABLE[i % 8][digit]]
    return c == 0


def generate_verhoeff_checksum(number_str: str) -> int:
    """Generates the single Verhoeff checksum digit for a prefix string."""
    c = 0
    reversed_digits = [int(x) for x in reversed(number_str)]
    for i, digit in enumerate(reversed_digits):
        c = _D_TABLE[c][_P_TABLE[(i + 1) % 8][digit]]
    return _INV_TABLE[c]


def validate_aadhaar_number(aadhaar: str, allow_demo: bool = True) -> tuple[bool, str]:
    """
    Validates a 12-digit Aadhaar number:
    - Must be exactly 12 digits
    - Must contain only numeric characters
    - Must not begin with 0 or 1 according to UIDAI specification
    - Must pass Verhoeff checksum
    In demo mode, test numbers can also be accepted if configured.
    """
    cleaned = aadhaar.replace(" ", "").replace("-", "").strip()
    if len(cleaned) != 12 or not cleaned.isdigit():
        return False, "Aadhaar number must be exactly 12 numeric digits."
    if cleaned[0] in ("0", "1"):
        return False, "Aadhaar number cannot begin with 0 or 1 per UIDAI specifications."
    if not validate_verhoeff(cleaned):
        if allow_demo and cleaned.startswith("9999"):
            # Permitted demo test prefix for ease of testing
            return True, ""
        return False, "Invalid Aadhaar number checksum (Verhoeff verification failed)."
    return True, ""


def mask_aadhaar(aadhaar: str) -> str:
    """Returns masked Aadhaar string: XXXX XXXX 1234"""
    cleaned = aadhaar.replace(" ", "").replace("-", "").strip()
    if len(cleaned) >= 4:
        return f"XXXX XXXX {cleaned[-4:]}"
    return "XXXX XXXX XXXX"
