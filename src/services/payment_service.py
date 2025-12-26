import uuid
import json
from typing import Dict, List
from datetime import datetime

from src.utils.constants import PaymentMethod
from src.config import config


class PaymentService:
    """Сервис для работы с платежами"""

    def __init__(self):
        self.price_per_day = config.payment.price_per_day
        self.payment_methods = config.payment.payment_methods

    def generate_payment_id(self) -> str:
        """Сгенерировать уникальный ID платежа"""
        return f"PAY-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    def generate_payment_details(self, method: PaymentMethod, amount: float) -> Dict:
        """Сгенерировать реквизиты для оплаты в зависимости от метода"""

        if method == PaymentMethod.CARD:
            return {
                "method": "card",
                "bank_name": "Тинькофф",
                "card_number": "5536 9138 1234 5678",
                "cardholder": "ИВАНОВ ИВАН",
                "amount": amount,
                "comment": self.generate_payment_comment()
            }

        elif method == PaymentMethod.QIWI:
            return {
                "method": "qiwi",
                "wallet": "+79001234567",
                "amount": amount,
                "comment": self.generate_payment_comment()
            }

        elif method == PaymentMethod.SBERBANK:
            return {
                "method": "sberbank",
                "card_number": "5469 3800 1234 5678",
                "amount": amount,
                "comment": self.generate_payment_comment()
            }

        elif method == PaymentMethod.YOOMONEY:
            return {
                "method": "yoomoney",
                "wallet": "410011234567890",
                "amount": amount,
                "comment": self.generate_payment_comment()
            }

        elif method == PaymentMethod.WEBMONEY:
            return {
                "method": "webmoney",
                "wallet": "R123456789012",
                "amount": amount,
                "comment": self.generate_payment_comment()
            }

        elif method == PaymentMethod.CRYPTO:
            return {
                "method": "crypto",
                "wallet": "0x742d35Cc6634C0532925a3b844Bc9e0a3A3A3A3A",
                "crypto": "USDT (TRC20)",
                "amount": amount,
                "comment": self.generate_payment_comment()
            }

        else:
            return {
                "method": method.value,
                "amount": amount,
                "comment": self.generate_payment_comment()
            }

    def generate_payment_comment(self) -> str:
        """Сгенерировать комментарий для платежа"""
        return f"VPN-{uuid.uuid4().hex[:6].upper()}"

    def generate_payment_url(self, payment_details: Dict) -> str:
        """Сгенерировать URL для онлайн-оплаты"""
        method = payment_details.get("method")

        if method == "card":
            # Для карт обычно нет прямой ссылки
            return None

        elif method == "qiwi":
            amount = payment_details.get("amount")
            comment = payment_details.get("comment")
            return f"https://qiwi.com/payment/form/99?extra%5B%27account%27%5D=+79001234567&amount={amount}&extra%5B%27comment%27%5D={comment}"

        elif method == "yoomoney":
            amount = payment_details.get("amount")
            return f"https://yoomoney.ru/transfer/quickpay?requestId=234567890&amount={amount}"

        else:
            return None

    def format_payment_message(self, payment_details: Dict, payment_id: str) -> str:
        """Форматировать сообщение с реквизитами для оплаты"""
        method = payment_details.get("method")
        amount = payment_details.get("amount")
        comment = payment_details.get("comment")

        message = f"💳 <b>Реквизиты для оплаты</b>\n\n"
        message += f"🆔 ID платежа: <code>{payment_id}</code>\n"
        message += f"💰 Сумма: <b>{amount}₽</b>\n"
        message += f"📝 Комментарий: <code>{comment}</code>\n\n"

        if method == "card":
            message += f"🏦 Банк: {payment_details.get('bank_name')}\n"
            message += f"💳 Номер карты: <code>{payment_details.get('card_number')}</code>\n"
            message += f"👤 Получатель: {payment_details.get('cardholder')}\n"

        elif method == "qiwi":
            message += f"🥝 QIWI кошелек: <code>{payment_details.get('wallet')}</code>\n"

        elif method == "sberbank":
            message += f"🟢 Сбербанк: <code>{payment_details.get('card_number')}</code>\n"

        elif method == "yoomoney":
            message += f"🟡 ЮMoney: <code>{payment_details.get('wallet')}</code>\n"

        elif method == "webmoney":
            message += f"🔵 WebMoney: <code>{payment_details.get('wallet')}</code>\n"

        elif method == "crypto":
            message += f"₿ Криптовалюта: {payment_details.get('crypto')}\n"
            message += f"👛 Кошелек: <code>{payment_details.get('wallet')}</code>\n"

        message += f"\n⚠️ <b>Внимание!</b>\n"
        message += f"• Обязательно укажите комментарий к платежу\n"
        message += f"• После оплаты отправьте скриншот чека\n"
        message += f"• Обычно подтверждение занимает до 15 минут\n\n"

        message += f"<i>Если вы уже оплатили, нажмите кнопку ниже</i>"

        return message


# Создаем глобальный экземпляр сервиса
payment_service = PaymentService()