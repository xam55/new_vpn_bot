from aiogram.fsm.state import State, StatesGroup


class AdminPanelStates(StatesGroup):
    """Состояния админ-панели"""

    main_menu = State()  # Главное меню админа

    # Управление подтверждениями
    confirmations_list = State()  # Список платежей для подтверждения
    payment_detail = State()  # Детали платежа
    confirm_payment = State()  # Подтверждение платежа
    reject_payment = State()  # Отклонение платежа с комментарием

    # Управление пользователями
    users_list = State()  # Список пользователей
    user_detail = State()  # Детали пользователя
    user_edit = State()  # Редактирование пользователя
    user_ban = State()  # Блокировка пользователя
    user_unban = State()  # Разблокировка пользователя
    make_admin = State()  # Назначение администратором

    # Управление ключами
    keys_list = State()  # Список всех ключей
    key_detail = State()  # Детали ключа
    key_edit = State()  # Редактирование ключа
    key_revoke = State()  # Отзыв ключа
    key_extend = State()  # Продление ключа

    # Статистика
    statistics_view = State()  # Просмотр статистики
    export_data = State()  # Экспорт данных

    # Настройки
    settings_menu = State()  # Меню настроек
    edit_price = State()  # Изменение цены
    edit_payment_methods = State()  # Изменение методов оплаты
    edit_ssh_settings = State()  # Изменение SSH настроек

    # Логи
    logs_view = State()  # Просмотр логов
    logs_filter = State()  # Фильтрация логов


class AdminBroadcastStates(StatesGroup):
    """Состояния для рассылки сообщений"""

    start_broadcast = State()  # Начало рассылки
    enter_broadcast_message = State()  # Ввод сообщения для рассылки
    select_broadcast_recipients = State()  # Выбор получателей
    confirm_broadcast = State()  # Подтверждение рассылки


class AdminSupportStates(StatesGroup):
    """Состояния для техподдержки"""

    waiting_user_message = State()  # Ожидание сообщения пользователя
    answering_user = State()  # Ответ пользователю
    view_conversation = State()  # Просмотр переписки