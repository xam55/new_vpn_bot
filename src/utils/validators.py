import re
from datetime import datetime
from typing import Optional


def validate_days_input(days_text: str, min_days: int = 1, max_days: int = 365) -> Optional[int]:
    """Валидация ввода количества дней"""
    try:
        days = int(days_text.strip())
        if min_days <= days <= max_days:
            return days
        return None
    except ValueError:
        return None


def validate_phone_number(phone: str) -> bool:
    """Валидация номера телефона"""
    # Простая проверка для российских номеров
    pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    return bool(re.match(pattern, phone))


def validate_email(email: str) -> bool:
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_ip_address(ip: str) -> bool:
    """Валидация IP адреса"""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False

    # Проверка октетов
    parts = ip.split('.')
    for part in parts:
        if not 0 <= int(part) <= 255:
            return False

    return True


def validate_wireguard_key(key: str) -> bool:
    """Валидация ключа WireGuard"""
    # Base64 ключ должен быть 44 символа
    pattern = r'^[A-Za-z0-9+/]{42,44}=?$'
    return bool(re.match(pattern, key))


def validate_amount(amount_str: str) -> Optional[float]:
    """Валидация суммы платежа"""
    try:
        amount = float(amount_str.replace(',', '.'))
        if amount > 0:
            return amount
        return None
    except (ValueError, TypeError):
        return None


def validate_date(date_str: str, fmt: str = "%Y-%m-%d") -> bool:
    """Валидация даты"""
    try:
        datetime.strptime(date_str, fmt)
        return True
    except ValueError:
        return False