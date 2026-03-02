import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


BOT_TOKEN = "6368649071:AAGd4-NxeEiTfpFz_IzIt7k3oEYDM8DyzYU"

AVERAGE_REEL_TIME = 30  # seconds per reel

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ===================================
# DATABASE SETUP
# ===================================
def init_db():
    conn = sqlite3.connect("reels_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            user_id INTEGER,
            date TEXT,
            screen_time REAL,
            reels INTEGER
        )
    """)
    conn.commit()
    conn.close()


def save_data(user_id, date, screen_time, reels):
    conn = sqlite3.connect("reels_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usage (user_id, date, screen_time, reels)
        VALUES (?, ?, ?, ?)
    """, (user_id, date, screen_time, reels))
    conn.commit()
    conn.close()


def get_data_range(user_id, start_date, end_date):
    conn = sqlite3.connect("reels_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT screen_time, reels FROM usage
        WHERE user_id = ? AND date BETWEEN ? AND ?
    """, (user_id, start_date, end_date))
    data = cursor.fetchall()
    conn.close()
    return data


def get_today_data(user_id, date):
    conn = sqlite3.connect("reels_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT screen_time, reels FROM usage
        WHERE user_id = ? AND date = ?
        ORDER BY ROWID DESC LIMIT 1
    """, (user_id, date))
    result = cursor.fetchone()
    conn.close()
    return result


# BOT COMMANDS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Instagram Reel Counter Bot!\n\n"
        "📩 Send Instagram screen time in minutes.\n"
        "Example: 45\n\n"
        "Commands:\n"
        "/today - Today's report\n"
        "/weekly - Weekly report\n"
        "/monthly - Monthly report"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        screen_time_minutes = float(update.message.text)

        screen_time_seconds = screen_time_minutes * 60
        estimated_reels = int(screen_time_seconds // AVERAGE_REEL_TIME)

        today = datetime.now().strftime("%Y-%m-%d")

        save_data(user_id, today, screen_time_minutes, estimated_reels)

        await update.message.reply_text(
            f"✅ Data Saved!\n\n"
            f"📊 Screen Time: {screen_time_minutes} minutes\n"
            f"🎬 Estimated Reels: {estimated_reels}"
        )

    except ValueError:
        await update.message.reply_text(
            "⚠️ Please send only number in minutes.\nExample: 45"
        )


# ===================================
# TODAY REPORT
# ===================================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    today_date = datetime.now().strftime("%Y-%m-%d")

    data = get_today_data(user_id, today_date)

    if data:
        screen_time, reels = data
        await update.message.reply_text(
            f"📅 Today's Report\n\n"
            f"⏳ Screen Time: {screen_time} minutes\n"
            f"🎬 Reels Watched: {reels}"
        )
    else:
        await update.message.reply_text("No data found for today.")


# ===================================
# WEEKLY REPORT
# ===================================
async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    data = get_data_range(
        user_id,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    if data:
        total_screen_time = sum(row[0] for row in data)
        total_reels = sum(row[1] for row in data)

        await update.message.reply_text(
            f"📊 Weekly Report (Last 7 Days)\n\n"
            f"⏳ Total Screen Time: {round(total_screen_time, 2)} minutes\n"
            f"🎬 Total Reels Watched: {total_reels}\n"
            f"📈 Average Per Day: {round(total_reels / 7, 2)} reels"
        )
    else:
        await update.message.reply_text("No data found for this week.")


# ===================================
# MONTHLY REPORT
# ===================================
async def monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    data = get_data_range(
        user_id,
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )

    if data:
        total_screen_time = sum(row[0] for row in data)
        total_reels = sum(row[1] for row in data)

        await update.message.reply_text(
            f"📊 Monthly Report (Last 30 Days)\n\n"
            f"⏳ Total Screen Time: {round(total_screen_time, 2)} minutes\n"
            f"🎬 Total Reels Watched: {total_reels}\n"
            f"📈 Average Per Day: {round(total_reels / 30, 2)} reels"
        )
    else:
        await update.message.reply_text("No data found for this month.")


# ===================================
# MAIN
# ===================================
def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("weekly", weekly))
    app.add_handler(CommandHandler("monthly", monthly))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
