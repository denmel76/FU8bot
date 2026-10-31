import aiosqlite

DB_NAME = "barber.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                service TEXT,
                master TEXT, 
                appointment_time TEXT,
                status TEXT DEFAULT 'new'
            )
        """)
        await db.commit()

async def save_appointment(user_id, name, service, master, appointment_time):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO appointments (user_id, name, service, master, appointment_time) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, service, master, appointment_time)
        )
        await db.commit()

async def get_user_appointments(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, service, master, appointment_time FROM appointments WHERE user_id = ? AND status = 'new' ORDER BY id DESC",
            (user_id,)
        )
        return await cursor.fetchall()

async def cancel_appointment(appointment_id, user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE appointments SET status = 'cancelled' WHERE id = ? AND user_id = ?",
            (appointment_id, user_id)
        )
        await db.commit()

# НОВАЯ ФУНКЦИЯ ДЛЯ АДМИНА
async def get_all_active_appointments():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, name, service, master, appointment_time, user_id FROM appointments WHERE status = 'new' ORDER BY id DESC"
        )
        return await cursor.fetchall()

