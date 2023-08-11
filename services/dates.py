import calendar
from datetime import datetime

import pytz

MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def get_last_day_of_month(date: datetime) -> datetime:
    year = date.year
    month = date.month

    _, num_days = calendar.monthrange(year, month)

    last_day = datetime(year, month, num_days)

    return last_day


def is_business_day(date: datetime) -> bool:
    if date.weekday() < 5:
        return True
    else:
        return False


def get_mes_ano_display(date: datetime) -> str:
    return f"{MESES[date.month]}/{date.year}"
