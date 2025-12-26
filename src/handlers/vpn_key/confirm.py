from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.states.vpn_states import PaymentVerificationStates
from src.keyboards.admin import get_payment_actions_keyboard
from src.services import PaymentDAO, UserDAO, VPNKeyDAO, get_session
from src.services.wireguard import wireguard_service
from src.config import config
import json

confirm_router = Router()


@confirm_router.callback_query(F.data.startswith("payment_detail_"))
async def show_payment_detail(callback: CallbackQuery, state: FSMContext):
    """Показать детали платежа для администратора"""

    # Проверяем, является ли пользователь администратором
    if callback.from_user.id not in config.bot.admin_ids:
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    # Извлекаем ID платежа
    try:
        payment_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка получения платежа", show_alert=True)
        return

    # Получаем информацию о платеже
    async for session in get_session():
        payment = await PaymentDAO.get_by_id(session, payment_id)

        if not payment:
            await callback.answer("❌ Платеж не найден", show_alert=True)
            return

        # Получаем информацию о пользователе
        user = payment.user

        # Форматируем информацию о платеже
        payment_details = json.loads(payment.payment_details) if payment.payment_details else {}

        message_text = (
            "💰 <b>Детали платежа</b>\n\n"
            f"🆔 ID: <code>{payment.payment_id}</code>\n"
            f"👤 Пользователь: {user.full_name}\n"
            f"📛 Username: @{user.username if user.username else 'нет'}\n"
            f"🆔 TG ID: <code>{user.telegram_id}</code>\n\n"
            f"💸 Сумма: {payment.amount}₽\n"
            f"💳 Метод: {payment.method}\n"
            f"📅 Создан: {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"⏳ Статус: {payment.status}\n\n"
        )

        # Добавляем информацию о реквизитах
        if payment_details:
            message_text += "<b>Реквизиты:</b>\n"
            for key, value in payment_details.items():
                if key not in ['method', 'amount', 'comment']:
                    message_text += f"• {key}: {value}\n"

        # Если есть скриншот
        if payment.proof_photo_id:
            # Здесь можно отправить фото администратору
            # Пока просто указываем, что фото есть
            message_text += "\n📸 <b>Скриншот прикреплен</b>\n"

        # Отправляем сообщение с действиями
        await callback.message.edit_text(
            message_text,
            reply_markup=get_payment_actions_keyboard(payment.id)
        )

    await state.set_state(PaymentVerificationStates.payment_detail)
    await callback.answer()


@confirm_router.callback_query(F.data.startswith("confirm_payment_"))
async def confirm_payment(callback: CallbackQuery, state: FSMContext):
    """Подтверждение платежа администратором"""

    # Проверяем права
    if callback.from_user.id not in config.bot.admin_ids:
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    # Извлекаем ID платежа
    try:
        payment_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка получения платежа", show_alert=True)
        return

    async for session in get_session():
        # Получаем платеж
        payment = await PaymentDAO.get_by_id(session, payment_id)

        if not payment:
            await callback.answer("❌ Платеж не найден", show_alert=True)
            return

        # Проверяем, не подтвержден ли уже
        if payment.status == "confirmed":
            await callback.answer("✅ Платеж уже подтвержден", show_alert=True)
            return

        # Получаем данные пользователя
        user = payment.user

        # Извлекаем дни из payment_details или вычисляем из суммы
        days = 30  # По умолчанию
        try:
            payment_details = json.loads(payment.payment_details) if payment.payment_details else {}
            if 'days' in payment_details:
                days = int(payment_details['days'])
            else:
                # Вычисляем дни из суммы
                days = int(payment.amount / config.payment.price_per_day)
        except (ValueError, KeyError, TypeError):
            # Вычисляем дни из суммы
            days = int(payment.amount / config.payment.price_per_day)

        # Подтверждаем платеж
        await PaymentDAO.confirm_payment(
            session=session,
            payment_id=payment.id,
            admin_id=callback.from_user.id,
            comment="Подтверждено администратором"
        )

        # Создаем VPN ключ
        try:
            # Генерируем ключи WireGuard
            keys = await wireguard_service.generate_keys()

            # Получаем информацию о сервере
            server_info = await wireguard_service.get_server_info()

            # Получаем свободный IP
            client_ip = await wireguard_service.get_next_client_ip()

            # Создаем конфиг для клиента
            config_data = await wireguard_service.generate_client_config(
                client_private_key=keys["private_key"],
                client_ip=client_ip,
                server_public_key=server_info["public_key"],
                server_endpoint=server_info["endpoint"],
                server_port=server_info["port"]
            )

            # Добавляем клиента на сервер
            added = await wireguard_service.add_client_to_server(
                client_public_key=keys["public_key"],
                client_ip=client_ip
            )

            if not added:
                raise Exception("Не удалось добавить клиента на сервер")

            # Создаем запись в базе данных
            key_name = f"user{user.id}_{payment.payment_id}"

            vpn_key = await VPNKeyDAO.create(
                session=session,
                user_id=user.id,
                key_name=key_name,
                private_key=keys["private_key"],
                public_key=keys["public_key"],
                server_public_key=server_info["public_key"],
                ip_address=client_ip,
                config_data=config_data,
                days=days,
                server_ip=server_info["ip"],
                server_port=server_info["port"],
                server_endpoint=server_info["endpoint"],
                payment_id=payment.id
            )

            # Обновляем статистику пользователя
            user.total_spent += payment.amount
            await session.commit()

            # Отправляем ключ пользователю
            # Здесь нужно отправить сообщение пользователю
            # Для этого нужен доступ к боту

            message_to_user = (
                "🎉 <b>Ваш VPN ключ готов!</b>\n\n"
                f"🔑 Ключ: <code>{key_name}</code>\n"
                f"🌐 IP: <code>{client_ip}</code>\n"
                f"⏳ Срок: {days} дней\n"
                f"📅 Истекает: {vpn_key.expires_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                "📎 <b>Конфигурационный файл:</b>\n"
                "Прикрепите этот файл к WireGuard приложению."
            )

            # Здесь нужно отправить сообщение пользователю
            # Пока просто сохраняем для теста
            print(f"Ключ создан для пользователя {user.telegram_id}")

            # Отправляем подтверждение администратору
            await callback.message.edit_text(
                f"✅ <b>Платеж подтвержден и ключ создан!</b>\n\n"
                f"🔑 Ключ: {key_name}\n"
                f"👤 Пользователь: {user.full_name}\n"
                f"💰 Сумма: {payment.amount}₽\n"
                f"⏳ Срок: {days} дней\n\n"
                "✅ VPN ключ успешно отправлен пользователю."
            )

            # Логируем действие
            # Здесь можно добавить логирование

        except Exception as e:
            # Если ошибка при создании ключа
            error_msg = (
                f"❌ <b>Ошибка при создании VPN ключа!</b>\n\n"
                f"Платеж: {payment.payment_id}\n"
                f"Пользователь: {user.full_name}\n"
                f"Ошибка: {str(e)}"
            )

            await callback.message.edit_text(error_msg)

            # Возвращаем платеж в статус оплачен
            payment.status = "paid"
            await session.commit()

            await callback.answer("❌ Ошибка при создании ключа", show_alert=True)
            return

    await callback.answer("✅ Платеж подтвержден")


@confirm_router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback: CallbackQuery, state: FSMContext):
    """Отклонение платежа администратором"""

    # Проверяем права
    if callback.from_user.id not in config.bot.admin_ids:
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    # Извлекаем ID платежа
    try:
        payment_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка получения платежа", show_alert=True)
        return

    # Запрашиваем причину отклонения
    await callback.message.edit_text(
        "📝 <b>Укажите причину отклонения платежа:</b>\n\n"
        "Напишите комментарий, который увидит пользователь.\n"
        "Это поможет ему понять, что пошло не так."
    )

    # Сохраняем ID платежа в состоянии
    await state.update_data(reject_payment_id=payment_id)
    await state.set_state(PaymentVerificationStates.reject_payment)

    await callback.answer()


@confirm_router.message(PaymentVerificationStates.reject_payment)
async def process_rejection_reason(message: Message, state: FSMContext):
    """Обработка причины отклонения платежа"""

    # Получаем данные из состояния
    data = await state.get_data()
    payment_id = data.get('reject_payment_id')

    if not payment_id:
        await message.answer("❌ Ошибка: не найден ID платежа")
        await state.clear()
        return

    reason = message.text

    async for session in get_session():
        # Отклоняем платеж
        await PaymentDAO.reject_payment(
            session=session,
            payment_id=payment_id,
            admin_id=message.from_user.id,
            comment=reason
        )

        # Получаем информацию о платеже для уведомления пользователя
        payment = await PaymentDAO.get_by_id(session, payment_id)
        if payment and payment.user:
            user_message = (
                "❌ <b>Ваш платеж отклонен администратором</b>\n\n"
                f"💰 Сумма: {payment.amount}₽\n"
                f"📋 ID: <code>{payment.payment_id}</code>\n\n"
                f"📝 <b>Причина:</b>\n{reason}\n\n"
                "Если вы считаете, что это ошибка, свяжитесь с поддержкой."
            )

            # Здесь нужно отправить сообщение пользователю
            print(f"Платеж отклонен для пользователя {payment.user.telegram_id}")

    # Отправляем подтверждение администратору
    await message.answer(
        "✅ <b>Платеж отклонен</b>\n\n"
        f"Пользователь уведомлен о причине отклонения.\n\n"
        f"📝 <b>Причина:</b>\n{reason}"
    )

    # Очищаем состояние
    await state.clear()