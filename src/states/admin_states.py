# src/states/admin_states.py
from aiogram.fsm.state import State, StatesGroup

class AdminPanelStates(StatesGroup):
    """Состояния админ-панели — включены все алиасы, которые используются в хендлерах."""

    # Главное меню админа
    main_menu = State()

    # ---- Подтверждения / платежи ----
    # используемые в разных вариантах кода: confirmations, confirmations_list
    confirmations = State()
    confirmations_list = State()
    payment_detail = State()
    confirm_payment = State()
    reject_payment = State()
    confirmation_view = State()

    # ---- Пользователи ----
    users_list = State()
    user_detail = State()
    user_edit = State()
    user_ban = State()
    user_unban = State()
    make_admin = State()

    # ---- Ключи ----
    keys_list = State()
    key_detail = State()
    key_edit = State()
    key_revoke = State()
    key_extend = State()

    # ---- Статистика и экспорт ----
    statistics_view = State()
    export_data = State()

    # ---- Настройки ----
    settings_menu = State()
    edit_price = State()
    edit_payment_methods = State()
    edit_ssh_settings = State()

    # ---- Логи ----
    logs_view = State()
    logs_filter = State()

# Дополнительные (если в будущем понадобятся) — можно переиспользовать эти имена
# (оставлены для совместимости с импорте/экспортом в других модулях)
