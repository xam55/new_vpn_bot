# WireGuard DNS и Keepalive
WG_DNS_SERVERS = ["1.1.1.1", "8.8.8.8"]
WG_KEEPALIVE = 25
# Способы оплаты (Enum)
from enum import Enum

class PaymentMethod(str, Enum):
	CARD = "card"
	QIWI = "qiwi"
	WEBMONEY = "webmoney"
	SBERBANK = "sberbank"
	YOOMONEY = "yoomoney"
	CRYPTO = "crypto"

class VPNKeyStatus(str, Enum):
	ACTIVE = "active"
	PENDING = "pending"
	REVOKED = "revoked"
	EXPIRED = "expired"

class PaymentStatus(str, Enum):
	PENDING = "pending"
	PAID = "paid"
	CONFIRMED = "confirmed"
	REJECTED = "rejected"
	EXPIRED = "expired"
# Цены
PRICE_PER_DAY = 10

# Лимиты
MAX_KEY_DURATION_DAYS = 365
MIN_KEY_DURATION_DAYS = 1

# Сообщения
START_MESSAGE = """
🤖 <b>Добро пожаловать в VPN Bot!</b>

Основные команды:
/vpnkey - Купить VPN ключ
/help - Помощь

Цены:
1 день - 10₽
30 дней - 300₽
365 дней - 3650₽
"""

HELP_MESSAGE = """
<b>📚 Помощь по использованию VPN Bot</b>

<b>Как купить VPN:</b>
1. Нажмите /vpnkey
2. Выберите срок действия
3. Оплатите счет
4. Отправьте скриншот оплаты
5. Получите VPN конфиг
"""