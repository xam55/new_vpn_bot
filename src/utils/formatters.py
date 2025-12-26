def format_key_info(key_info: dict) -> str:
    """Форматирование информации о VPN-ключе для пользователя"""
    text = (
        f"🔑 <b>Ключ:</b> <code>{key_info.get('key_name','')}</code>\n"
        f"🌐 <b>IP:</b> <code>{key_info.get('ip_address','')}</code>\n"
        f"⏳ <b>Статус:</b> {key_info.get('status','')}\n"
        f"📅 <b>Создан:</b> {key_info.get('created_at').strftime('%d.%m.%Y') if key_info.get('created_at') else ''}\n"
        f"📅 <b>Истекает:</b> {key_info.get('expires_at').strftime('%d.%m.%Y') if key_info.get('expires_at') else ''}\n"
    )
    if key_info.get('traffic_limit'):
        text += f"📊 <b>Трафик:</b> {key_info.get('traffic_used',0)}/{key_info.get('traffic_limit')} ГБ\n"
    if key_info.get('server_ip'):
        text += f"🖥 <b>Сервер:</b> <code>{key_info.get('server_ip')}</code>"
    return text
from datetime import datetime


def format_price(amount: float) -> str:
    """Форматирование цены"""
    return f"{amount:,.0f}₽".replace(",", " ")


def format_date(date: datetime) -> str:
    """Форматирование даты"""
    return date.strftime("%d.%m.%Y %H:%M")


def format_time_left(expires_at: datetime) -> str:
    """Форматирование оставшегося времени"""
    now = datetime.now()
    if expires_at < now:
        return "Истек"

    delta = expires_at - now
    days = delta.days
    hours = delta.seconds // 3600

    if days > 0:
        return f"{days} дней"
    elif hours > 0:
        return f"{hours} часов"
    else:
        return f"{delta.seconds // 60} минут"