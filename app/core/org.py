"""Fictional employer identity used in codes, emails, and product copy."""

ORG_NAME = "ESMINCUBYTE"
EMPLOYEE_CODE_PREFIX = "ESMINCUBYTE"
EMAIL_DOMAIN = "esmincubyte.example"
HR_EMAIL = f"hr.manager@{EMAIL_DOMAIN}"


def format_employee_code(index: int) -> str:
    return f"{EMPLOYEE_CODE_PREFIX}-{index:05d}"


def org_email(local_part: str) -> str:
    return f"{local_part}@{EMAIL_DOMAIN}"
