from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime

from src.states.vpn_states import VPNKeyManagementStates
from src.keyboards import (
    get_user_keys_keyboard,
    get_key_actions_keyboard,
    get_back_keyboard
)
from src.services import VPNKeyDAO, UserDAO, get_session
from src.utils.formatters import format_key_info, format_time_left

status_router = Router()
router = status_router



@router.message(Command("mystatus"))
@router.message(F.text == "📋 Мои ключи")
async def cmd_my_status(message: Message, state: FSMContext):
    """Показать статус ключей пользователя"""

    await state.clear()

    async for session in get_session():
        # Получаем пользователя
        user = await UserDAO.get_by_telegram_id(session, message.from_user.id)

        if not user:
            await message.answer(
                "❌ <b>Вы не зарегистрированы в системе</b>\n\n"
                "Нажмите /start для регистрации."
            )
            return

        # Получаем активные ключи пользователя
        keys = await VPNKeyDAO.get_user_keys(session, user.id, active_only=True)

        if not keys:
            await message.answer(
                "🔍 <b>У вас нет активных VPN ключей</b>\n\n"
                "Чтобы приобрести VPN ключ, нажмите /vpnkey",
                reply_markup=get_user_keys_keyboard([])
            )
            return

        # Формируем сообщение
        message_text = (
            f"📋 <b>Ваши активные VPN ключи</b>\n\n"
            f"Всего ключей: {len(keys)}\n\n"
        )

        # Показываем первые 3 ключа
        for i, key in enumerate(keys[:3], 1):
            days_left = key.days_left
            message_text += (
                f"{i}. <b>{key.key_name}</b>\n"
                f"   🌐 IP: <code>{key.ip_address}</code>\n"
                f"   ⏳ Осталось: {days_left} дней\n"
                f"   📅 Истекает: {key.expires_at.strftime('%d.%m.%Y')}\n\n"
            )

        if len(keys) > 3:
            message_text += f"<i>И еще {len(keys) - 3} ключей...</i>\n\n"

        message_text += "Выберите ключ для управления:"

        await message.answer(
            message_text,
            reply_markup=get_user_keys_keyboard(keys)
        )

    await state.set_state(VPNKeyManagementStates.view_key)


@router.callback_query(F.data.startswith("key_info_"))
async def show_key_info(callback: CallbackQuery, state: FSMContext):
    """Показать информацию о конкретном ключе"""

    # Извлекаем ID ключа
    try:
        key_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка получения ключа", show_alert=True)
        return

    async for session in get_session():
        # Получаем ключ
        key = await VPNKeyDAO.get_by_id(session, key_id)

        if not key:
            await callback.answer("❌ Ключ не найден", show_alert=True)
            return

        # Проверяем, что ключ принадлежит пользователю
        if key.user.telegram_id != callback.from_user.id:
            await callback.answer("❌ Это не ваш ключ", show_alert=True)
            return

        # Формируем информацию о ключе
        key_info = {
            "id": key.id,
            "key_name": key.key_name,
            "status": key.status,
            "ip_address": key.ip_address,
            "created_at": key.created_at,
            "expires_at": key.expires_at,
            "traffic_used": key.traffic_used,
            "traffic_limit": key.traffic_limit,
            "server_ip": key.server_ip,
            "server_port": key.server_port,
            "user": {
                "full_name": key.user.full_name,
                "username": key.user.username
            }
        }

        message_text = format_key_info(key_info)

        await callback.message.edit_text(
            message_text,
            reply_markup=get_key_actions_keyboard(key.id)
        )

    await state.set_state(VPNKeyManagementStates.view_key)
    await callback.answer()


@router.callback_query(F.data.startswith("download_"))
async def download_key_config(callback: CallbackQuery):
    """Скачать конфигурационный файл ключа"""

    try:
        key_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка получения ключа", show_alert=True)
        return

    async for session in get_session():
        key = await VPNKeyDAO.get_by_id(session, key_id)

        if not key:
            await callback.answer("❌ Ключ не найден", show_alert=True)
            return

        # Проверяем права доступа
        if key.user.telegram_id != callback.from_user.id:
            await callback.answer("❌ Это не ваш ключ", show_alert=True)
            return

        # Проверяем, активен ли ключ
        if not key.is_active:
            await callback.answer("❌ Ключ не активен", show_alert=True)
            return

        # Отправляем конфиг как файл
        config_bytes = key.config_data.encode('utf-8')

        # Здесь нужно отправить файл
        # await callback.message.answer_document(
        #     document=BufferedInputFile(config_bytes, filename=f"{key.key_name}.conf"),
        #     caption=f"🔑 Конфигурационный файл: {key.key_name}"
        # )

        # Пока просто выводим информацию
        await callback.message.answer(
            f"📥 <b>Конфигурационный файл:</b>\n\n"
            f"Имя файла: <code>{key.key_name}.conf</code>\n\n"
            "<b>Содержимое:</b>\n"
            "<code>" + key.config_data[:500] + ("..." if len(key.config_data) > 500 else "") + "</code>"
        )

    await callback.answer()


@router.callback_query(F.data == "back_to_keys")
async def back_to_keys_list(callback: CallbackQuery, state: FSMContext):
    """Вернуться к списку ключей"""
    await cmd_my_status(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("delete_"))
async def delete_key_confirmation(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления ключа"""

    try:
        key_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка получения ключа", show_alert=True)
        return

    async for session in get_session():
        key = await VPNKeyDAO.get_by_id(session, key_id)

        if not key:
            await callback.answer("❌ Ключ не найден", show_alert=True)
            return

        # Проверяем права доступа
        if key.user.telegram_id != callback.from_user.id:
            await callback.answer("❌ Это не ваш ключ", show_alert=True)
            return

        await callback.message.edit_text(
            "🗑 <b>Вы уверены, что хотите удалить этот ключ?</b>\n\n"
            f"🔑 Ключ: <code>{key.key_name}</code>\n"
            f"🌐 IP: <code>{key.ip_address}</code>\n"
            f"⏳ Осталось дней: {key.days_left}\n\n"
            "⚠️ <i>Это действие нельзя отменить!</i>\n"
            "Ключ будет удален с сервера и перестанет работать.",
            reply_markup=get_confirmation_keyboard()
        )

    await state.update_data(delete_key_id=key_id)
    await state.set_state(VPNKeyManagementStates.delete_key_confirm)
    await callback.answer()


@router.callback_query(F.data == "refresh_keys")
async def refresh_keys_list(callback: CallbackQuery, state: FSMContext):
    """Обновить список ключей"""
    await cmd_my_status(callback.message, state)
    await callback.answer("Список обновлен")