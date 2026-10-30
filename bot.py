import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import TOKEN, ADMIN_ID, SERVICES, TEXTS
from database import init_db, save_appointment, get_user_appointments, cancel_appointment

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
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_appointments")],
        [InlineKeyboardButton(text="📞 Связаться с мастером", callback_data="contact")]
    ])
    await message.answer(TEXTS["start"], reply_markup=keyboard)

# --- КНОПКА НАЗАД ---
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_appointments")],
        [InlineKeyboardButton(text="📞 Связаться с мастером", callback_data="contact")]
    ])
    await callback.message.edit_text(TEXTS["start"], reply_markup=keyboard)
    await callback.answer()

# --- МОИ ЗАПИСИ И ОТМЕНА ---
@dp.callback_query(F.data == "my_appointments")
async def show_my_appointments(callback: CallbackQuery):
    appointments = await get_user_appointments(callback.from_user.id)
    
    if not appointments:
        await callback.message.edit_text(
            "У вас пока нет активных записей.", 
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]])
        )
    else:
        text = "📋 **Ваши записи:**\n\n"
        buttons = []
        for app in appointments:
            app_id, service, time = app
            text += f"• {service} — {time}\n"
            buttons.append([InlineKeyboardButton(text=f"❌ Отменить {time}", callback_data=f"cancel_{app_id}")])
        
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")])
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    
    await callback.answer()

@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_app(callback: CallbackQuery):
    app_id = int(callback.data.split("_")[1])
    await cancel_appointment(app_id, callback.from_user.id)
    
    await callback.message.edit_text(
        "❌ Запись успешно отменена. Ждем вас в другой раз!", 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]])
    )
    await callback.answer("Запись отменена")

# --- СВЯЗАТЬСЯ С МАСТЕРОМ ---
@dp.callback_query(F.data == "contact")
async def contact_master(callback: CallbackQuery):
    await callback.message.answer("Если у вас есть вопросы, напишите нашему мастеру: @Ваш_Юзернейм (замените в коде)")
    await callback.answer()

# --- ПРОЦЕСС ЗАПИСИ ---
@dp.callback_query(F.data == "book")
async def start_booking(callback: CallbackQuery, state: FSMContext):
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
    
    await save_appointment(message.from_user.id, name, service, time)
    
    admin_text = f"🔥 **Новая запись!**\n\n👤 Имя: {name}\n✂️ Услуга: {service}\n⏰ Время: {time}\n🆔 Клиент ID: {message.from_user.id}"
    if ADMIN_ID != 0:
        try:
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    
    await message.answer(TEXTS["success"].format(name=name, service=service, time=time))
    await state.clear()

async def main():
    await init_db()
    print("Barber Bot (v2) запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
