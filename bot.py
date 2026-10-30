import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, ADMIN_ID, SERVICES, TEXTS
from database import init_db, save_appointment, get_user_appointments

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class BookingState(StatesGroup):
    waiting_for_service = State()
    waiting_for_name = State()
    waiting_for_time = State()

# --- ГЛАВНОЕ МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_appointments")]
    ])
    await message.answer(TEXTS["start"], reply_markup=keyboard)

@dp.callback_query(F.data == "my_appointments")
async def show_my_appointments(callback: CallbackQuery):
    appointments = await get_user_appointments(callback.from_user.id)
    
    if not appointments:
        await callback.message.answer("У вас пока нет активных записей.")
    else:
        text = "📋 **Ваши записи:**\n\n"
        for app in appointments:
            text += f"• {app[0]} — {app[1]}\n"
        await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

# --- ПРОЦЕСС ЗАПИСИ ---
@dp.callback_query(F.data == "book")
async def start_booking(callback: CallbackQuery, state: FSMContext):
    # Создаем кнопки из словаря SERVICES
    buttons = []
    for key, value in SERVICES.items():
        buttons.append([InlineKeyboardButton(text=value, callback_data=f"srv_{key}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(TEXTS["choose_service"], reply_markup=keyboard)
    await state.set_state(BookingState.waiting_for_service)

@dp.callback_query(BookingState.waiting_for_service, F.data.startswith("srv_"))
async def process_service(callback: CallbackQuery, state: FSMContext):
    service_key = callback.data.split("_")[1]
    service_name = SERVICES.get(service_key)
    
    await state.update_data(service=service_name)
    await callback.message.edit_text(TEXTS["enter_name"])
    await state.set_state(BookingState.waiting_for_name)

@dp.message(BookingState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(TEXTS["enter_time"])
    await state.set_state(BookingState.waiting_for_time)

@dp.message(BookingState.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data['name']
    service = user_data['service']
    time = message.text
    
    # Сохраняем в базу
    await save_appointment(message.from_user.id, name, service, time)
    
    # Отправляем уведомление админу (вам)
    admin_text = f"🔥 **Новая запись!**\n\n👤 Имя: {name}\n✂️ Услуга: {service}\n⏰ Время: {time}\n🆔 Клиент ID: {message.from_user.id}"
    if ADMIN_ID != 0:
        try:
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    
    # Отвечаем клиенту
    await message.answer(TEXTS["success"].format(name=name, service=service, time=time))
    await state.clear()

async def main():
    await init_db()
    print("Barber Bot запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
