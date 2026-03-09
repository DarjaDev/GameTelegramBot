import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os
import threading
from flask import Flask

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

professions = ["Врач", "Инженер", "Фермер", "Военный", "Биолог", "Повар", "Механик", "Учитель"]
health_status = ["Полностью здоров", "Астма", "Диабет", "Слепота на один глаз", "Депрессия", "Аллергия"]
skills = ["Охота", "Садоводство", "Программирование", "Ремонт техники", "Игра на гитаре"]
items = ["Аптечка", "Семена растений", "Оружие", "Ноутбук", "Набор инструментов"]
fears = ["Клаустрофобия", "Страх крови", "Боязнь темноты"]

catastrophes = [
    "Ядерная война",
    "Вирусная пандемия",
    "Метеоритный дождь",
    "Экологическая катастрофа",
    "Роботический бунт"
]

participants = []  # [{"id":int, "name":str, "character":dict}]
votes = {}  # {voter_id: target_id}
game_started = False
catastrophe = ""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот 'Бункер'.\n"
        "/join — присоединиться к игре\n"
        "/startgame — раздать персонажей и начать игру\n"
        "/vote <имя> — голосовать за исключение игрока\n"
        "/results — показать текущие голоса"
    )


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if game_started:
        await update.message.reply_text("Игра уже началась, присоединиться нельзя.")
        return

    user = update.effective_user
    if user.id not in [p["id"] for p in participants]:
        participants.append({"id": user.id, "name": user.first_name})
        await update.message.reply_text(f"{user.first_name} присоединился к игре!")
    else:
        await update.message.reply_text("Вы уже в списке участников.")


async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global game_started, catastrophe

    if game_started:
        await update.message.reply_text("Игра уже началась.")
        return

    num_players = len(participants)
    if num_players > len(professions):
        await update.message.reply_text(
            "Слишком много игроков! Добавьте больше профессий/характеристик или уменьшите игроков.")
        return

    # Случайный сценарий катастрофы
    catastrophe = random.choice(catastrophes)
    await update.message.reply_text(f"Сценарий катастрофы: {catastrophe}")

    # Раздаём уникальные персонажи
    assigned_professions = random.sample(professions, num_players)
    assigned_health = random.sample(health_status, num_players)
    assigned_skills = random.sample(skills, num_players)
    assigned_items = random.sample(items, num_players)
    assigned_fears = random.sample(fears, num_players)

    for i, player in enumerate(participants):
        character = {
            "profession": assigned_professions[i],
            "health": assigned_health[i],
            "skill": assigned_skills[i],
            "item": assigned_items[i],
            "fear": assigned_fears[i]
        }
        player["character"] = character

        text = (
            f"Ваш персонаж для 'Бункера':\n"
            f"👤 Имя: {player['name']}\n"
            f"💼 Профессия: {character['profession']}\n"
            f"❤️ Состояние здоровья: {character['health']}\n"
            f"🛠 Навык: {character['skill']}\n"
            f"🎒 Предмет: {character['item']}\n"
            f"😱 Фобия: {character['fear']}"
        )
        await context.bot.send_message(chat_id=player["id"], text=text)

    game_started = True
    await update.message.reply_text("Персонажи разданы! Начинайте голосование с /vote <имя>")


async def players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not participants:
        await update.message.reply_text("Пока нет ни одного игрока.")
        return

    text = "Список игроков:\n"
    for i, player in enumerate(participants, 1):
        text += f"{i}. {player['name']}\n"

    await update.message.reply_text(text)


async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game_started:
        await update.message.reply_text("Игра ещё не началась.")
        return

    voter_id = update.effective_user.id
    if len(context.args) == 0:
        await update.message.reply_text("Укажите имя игрока для голосования: /vote <имя>")
        return

    target_name = context.args[0]
    target = next((p for p in participants if p["name"].lower() == target_name.lower()), None)
    if not target:
        await update.message.reply_text("Игрок с таким именем не найден.")
        return

    votes[voter_id] = target["id"]
    await update.message.reply_text(f"Вы проголосовали за исключение {target['name']}.")


async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not votes:
        await update.message.reply_text("Голосов пока нет.")
        return

    tally = {}
    for target_id in votes.values():
        tally[target_id] = tally.get(target_id, 0) + 1

    results_text = "Текущие голоса:\n"
    for target_id, count in tally.items():
        name = next(p["name"] for p in participants if p["id"] == target_id)
        results_text += f"{name}: {count} голосов\n"

    await update.message.reply_text(results_text)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("join", join))
app.add_handler(CommandHandler("startgame", startgame))
app.add_handler(CommandHandler("players", players))
app.add_handler(CommandHandler("vote", vote))
app.add_handler(CommandHandler("results", results))

    # ======= Keep-alive Web Server for Render =======
web_app = Flask("keepalive")

@web_app.route("/")
def home():
        return "Bot is running!"

def run_bot():
         # Start Flask server on Render's port
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    # Start bot in a daemon thread
    threading.Thread(target=run_bot, daemon=True).start()
    app.run_polling()


