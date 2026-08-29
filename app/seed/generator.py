from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.core.fx import get_fx_rate
from app.core.org import EMAIL_DOMAIN, format_employee_code
from app.employees.models import JOB_LEVELS

DEPARTMENTS = (
    "Engineering",
    "Product",
    "Design",
    "Sales",
    "Marketing",
    "Finance",
    "People",
    "Operations",
)

COUNTRIES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("United States", "USD", ("New York", "Austin", "Seattle", "Chicago")),
    ("United Kingdom", "GBP", ("London", "Manchester", "Edinburgh")),
    ("India", "INR", ("Bengaluru", "Hyderabad", "Pune", "Mumbai")),
    ("Germany", "EUR", ("Berlin", "Munich", "Hamburg")),
    ("Canada", "CAD", ("Toronto", "Vancouver", "Montreal")),
    ("Singapore", "SGD", ("Singapore",)),
    ("Australia", "AUD", ("Sydney", "Melbourne")),
    ("Brazil", "BRL", ("Sao Paulo", "Rio de Janeiro")),
    ("Netherlands", "EUR", ("Amsterdam", "Rotterdam")),
    ("Japan", "JPY", ("Tokyo", "Osaka")),
)

COUNTRY_USD_MULT = {
    "United States": Decimal("1.00"),
    "United Kingdom": Decimal("0.92"),
    "Germany": Decimal("0.90"),
    "Netherlands": Decimal("0.88"),
    "Canada": Decimal("0.85"),
    "Singapore": Decimal("0.95"),
    "Australia": Decimal("0.88"),
    "Japan": Decimal("0.80"),
    "Brazil": Decimal("0.45"),
    "India": Decimal("0.32"),
}

DEPT_USD_MULT = {
    "Engineering": Decimal("1.10"),
    "Product": Decimal("1.06"),
    "Design": Decimal("1.00"),
    "Sales": Decimal("1.08"),
    "Marketing": Decimal("0.96"),
    "Finance": Decimal("1.02"),
    "People": Decimal("0.94"),
    "Operations": Decimal("0.90"),
}

# Believable USD bands by level before country/department multipliers.
LEVEL_BANDS_USD: dict[str, tuple[Decimal, Decimal]] = {
    "IC1": (Decimal("42000"), Decimal("68000")),
    "IC2": (Decimal("62000"), Decimal("92000")),
    "IC3": (Decimal("85000"), Decimal("125000")),
    "IC4": (Decimal("115000"), Decimal("165000")),
    "IC5": (Decimal("150000"), Decimal("210000")),
    "IC6": (Decimal("185000"), Decimal("260000")),
    "M1": (Decimal("110000"), Decimal("160000")),
    "M2": (Decimal("145000"), Decimal("200000")),
    "M3": (Decimal("180000"), Decimal("250000")),
    "M4": (Decimal("220000"), Decimal("320000")),
}

TITLES = {
    "Engineering": {
        "IC1": "Software Engineer I",
        "IC2": "Software Engineer II",
        "IC3": "Software Engineer III",
        "IC4": "Senior Software Engineer",
        "IC5": "Staff Software Engineer",
        "IC6": "Principal Engineer",
        "M1": "Engineering Manager",
        "M2": "Senior Engineering Manager",
        "M3": "Director of Engineering",
        "M4": "VP Engineering",
    },
    "default": {
        "IC1": "Associate",
        "IC2": "Specialist",
        "IC3": "Analyst",
        "IC4": "Senior Specialist",
        "IC5": "Staff Specialist",
        "IC6": "Principal",
        "M1": "Manager",
        "M2": "Senior Manager",
        "M3": "Director",
        "M4": "Vice President",
    },
}

FIRST_NAMES = (
    "Aisha",
    "Alex",
    "Amir",
    "Ana",
    "Andre",
    "Aria",
    "Ben",
    "Camila",
    "Chen",
    "Clara",
    "Diego",
    "Elena",
    "Farah",
    "Felix",
    "Grace",
    "Hiro",
    "Imani",
    "Ivan",
    "Jade",
    "Jonas",
    "Kai",
    "Lena",
    "Luis",
    "Maya",
    "Mei",
    "Noah",
    "Omar",
    "Priya",
    "Quinn",
    "Ravi",
    "Sofia",
    "Tariq",
    "Uma",
    "Victor",
    "Wei",
    "Yara",
    "Zane",
    "Nora",
    "Sam",
    "Leila",
)

LAST_NAMES = (
    "Ahmed",
    "Baker",
    "Chen",
    "Costa",
    "Dubois",
    "Evans",
    "Fernandez",
    "Garcia",
    "Hassan",
    "Ito",
    "Johansson",
    "Khan",
    "Lopez",
    "Muller",
    "Nair",
    "Okafor",
    "Patel",
    "Rossi",
    "Silva",
    "Tanaka",
    "Usman",
    "Vargas",
    "Wright",
    "Young",
    "Zhang",
    "Kowalski",
    "Berg",
    "Novak",
    "Singh",
    "Kim",
)

STATUSES = ("ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "ON_LEAVE", "TERMINATED")


@dataclass(frozen=True)
class SeedEmployee:
    employee_code: str
    first_name: str
    last_name: str
    email: str
    country: str
    city: str
    department: str
    job_title: str
    job_level: str
    employment_status: str
    hire_date: date
    annual_salary: Decimal
    currency: str
    fx_rate_to_usd: Decimal
    annual_salary_usd: Decimal


def generate_employees(count: int, seed: int) -> list[SeedEmployee]:
    rng = random.Random(seed)
    used_emails: set[str] = set()
    rows: list[SeedEmployee] = []
    for index in range(1, count + 1):
        country, currency, cities = rng.choice(COUNTRIES)
        department = rng.choice(DEPARTMENTS)
        level = rng.choice(JOB_LEVELS)
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        email = _unique_email(first, last, index, used_emails)
        titles = TITLES.get(department, TITLES["default"])
        title = titles.get(level, TITLES["default"][level])
        if department != "Engineering":
            title = f"{department} {TITLES['default'][level]}"
        hire = date(2014, 1, 1) + timedelta(days=rng.randint(0, 12 * 365))
        salary, rate, usd = _salary_for(rng, country, department, level, currency)
        rows.append(
            SeedEmployee(
                employee_code=format_employee_code(index),
                first_name=first,
                last_name=last,
                email=email,
                country=country,
                city=rng.choice(cities),
                department=department,
                job_title=title,
                job_level=level,
                employment_status=rng.choice(STATUSES),
                hire_date=hire,
                annual_salary=salary,
                currency=currency,
                fx_rate_to_usd=rate,
                annual_salary_usd=usd,
            )
        )
    return rows


def _unique_email(first: str, last: str, index: int, used: set[str]) -> str:
    base = f"{first}.{last}.{index}@{EMAIL_DOMAIN}".lower()
    email = base
    suffix = 1
    while email in used:
        email = f"{first}.{last}.{index}.{suffix}@{EMAIL_DOMAIN}".lower()
        suffix += 1
    used.add(email)
    return email


def _salary_for(
    rng: random.Random, country: str, department: str, level: str, currency: str
) -> tuple[Decimal, Decimal, Decimal]:
    low, high = LEVEL_BANDS_USD[level]
    # Deterministic point inside the level band, then country and department.
    span = high - low
    pick = low + span * Decimal(str(rng.uniform(0.15, 0.90)))
    usd = pick * COUNTRY_USD_MULT[country] * DEPT_USD_MULT[department]
    usd = usd.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    rate = get_fx_rate(currency)
    local = usd / rate
    local = _round_local(local, currency)
    usd = (local * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return local, rate, usd


def _round_local(amount: Decimal, currency: str) -> Decimal:
    if currency == "JPY":
        return amount.quantize(Decimal("1000"), rounding=ROUND_HALF_UP)
    if currency == "INR":
        return amount.quantize(Decimal("1000"), rounding=ROUND_HALF_UP)
    return amount.quantize(Decimal("100"), rounding=ROUND_HALF_UP)
