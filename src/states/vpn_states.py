from aiogram.fsm.state import State, StatesGroup


from aiogram.fsm.state import State, StatesGroup


class VPNPurchaseStates(StatesGroup):
    select_duration = State()
    custom_duration = State()
    select_payment_method = State()
    waiting_payment = State()
    waiting_payment_proof = State()


class VPNKeyManagementStates(StatesGroup):
    """Состояния для управления ключами"""

    view_key = State()  # Просмотр информации о ключе
    renew_key = State()  # Продление ключа
    delete_key_confirm = State()  # Подтверждение удаления ключа


class PaymentVerificationStates(StatesGroup):
    """Состояния для верификации платежа"""

    waiting_admin_confirmation = State()  # Ожидание подтверждения от админа
    payment_confirmed = State()  # Платеж подтвержден
    payment_rejected = State()  # Платеж отклонен
    reject_payment = State()  # Ввод причины отклонения