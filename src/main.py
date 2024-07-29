import yaml
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from datetime import datetime

from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hi there! Please give me a password with /login command")

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage /login <password>")
        return

    db = context.bot_data['db']
    config = context.bot_data['config']

    if db.is_logged_in(update.effective_chat.id):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are already logged in!")
        return

    password = context.args[0]
    if password == config['password']:
        db.login(update.effective_chat.id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome! You are now logged in!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid password")

async def check_login(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    db = context.bot_data['db']
    if not db.is_logged_in(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="You are not logged in. Please login with /login command")
        return False
    return True

async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_login(update.effective_chat.id, context):
        return
    
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /channel list|subscribe|unsubscribe|show")
        return
    
    db = context.bot_data['db']
    config = context.bot_data['config']

    command = context.args[0]
    if command == 'list':
        text = ""
        for t in sorted(config['channels']):
            text += f"- {t}\n"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Available channels:\n{text}")
    elif command == 'subscribe':
        if len(context.args) < 2:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /channel subscribe <channel>")
            return
        
        channel = context.args[1]
        if channel not in config['channels']:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid channel")
            return
        
        if db.is_subscribed(update.effective_chat.id, channel):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You are already subscribed to " + channel)
            return

        db.subscribe(update.effective_chat.id, channel)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are now subscribed to " + channel)
    elif command == 'unsubscribe':
        if len(context.args) < 2:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /channel unsubscribe <channel>")
            return
        
        channel = context.args[1]
        if channel not in config['channels']:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid channel")
            return

        if not db.is_subscribed(update.effective_chat.id, channel):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You are not subscribed to " + channel)
            return
        
        db.unsubscribe(update.effective_chat.id, channel)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are now unsubscribed from " + channel)
    elif command == 'show':
        if len(context.args) < 2:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /channel show <channel>")
            return
        
        channel = context.args[1]
        if channel not in config['channels']:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid channel")
            return

        schedules = [s for s in db.get_schedules() if s['channel'] == channel]
        text = ""
        if len(schedules) == 0:
            text = "No schedules for this channel"
        else:
            text = f"Schedules for {channel}:\n\n"
            for s in schedules:
                for m in config['messages']:
                    if m['id'] == s['message']:
                        text += f"*{m['title']}*\n scheduled on {s['date']} {s['time']}\nRemove:```\n/schedule remove {m['id']} {channel} {s["date"]} {s["time"]}```\n\n"
        #text = text.replace('_', r'\_')
        print(text)
        print(text[121:])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid command")

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_login(update.effective_chat.id, context):
        return
    
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /message <list>")
        return
    
    db = context.bot_data['db']
    config = context.bot_data['config']

    command = context.args[0]
    if command == 'list':
        text = ""
        for m in sorted(config['messages'], key=lambda x: x['id']):
            text += f"{m['id']}:\n{m['text']}\n\n"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Available messages:\n{text}")

    elif command == 'show':
        if len(context.args) < 2:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /message show <message_id>")
            return
        
        message_id = context.args[1]
        message = [m for m in config['messages'] if m['id'] == message_id]
        if len(message) == 0:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid message_id")
            return
        
        message = message[0]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*{message['title']}*\n{message['text']}", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid command")

async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_login(update.effective_chat.id, context):
        return
    
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /schedule add|remove <message_id>")
        return
    

    db = context.bot_data['db']
    config = context.bot_data['config'] 

    command = context.args[0]
    if command == 'add':
        if len(context.args) < 4:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /schedule add <message_id> <channel_id> <date> [time]")
            return
        
        message_id = context.args[1]
        channel_id = context.args[2]
        date = context.args[3]
        time = context.args[4] if len(context.args) > 4 else config['default_time']

        try:
            x = datetime.strptime(date, '%d.%m.%y')
            print(x)
        except ValueError:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid date format. Use dd.mm.yy")
            return
        
        try:
            x = datetime.strptime(time, '%H:%M')
            print(x)
        except ValueError:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid time format. Use hh:mm")
            return

        if not message_id in [m['id'] for m in config['messages']]:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid message_id")
            return
        
        db.schedule(message_id, channel_id, date, time)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Message scheduled!")
    
    elif command == 'remove':
        if len(context.args) < 2:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /schedule remove <message_id> <channel> <date> <time>")
            return
        
        message_id = context.args[1]
        channel_id = context.args[2]
        date = context.args[3]
        time = context.args[4]

        schedules = db.get_schedules()
        for s in schedules:
            if s['message'] == message_id and s['date'] == date and s['time'] == time and s['channel'] == channel_id:
                db.remove_schedule(s)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Schedule removed!")
                return

    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid command!")

async def check_schedules(context: ContextTypes.DEFAULT_TYPE):
    print("Checking schedules", flush=True)
    db = context.bot_data['db']
    config = context.bot_data['config']

    schedules = db.get_schedules()
    now = datetime.now()
    for s in schedules:
        date = datetime.strptime(s['date'] + ' ' + s['time'], '%d.%m.%y %H:%M')
        if now >= date:
            for m in config['messages']:
                if m['id'] == s['message']:
                    for chat_id in db.get_subscribed_chats(s['channel']):
                        await context.bot.send_message(chat_id=chat_id, text=f"*{m['title']}*\n{m['text']}", parse_mode='Markdown')
            db.remove_schedule(s) 

if __name__ == '__main__':
    db = Database('database.yml')

    with open('config.yml', 'r', encoding="utf-8") as config_file:
        config = yaml.load(config_file, yaml.BaseLoader)

    application = ApplicationBuilder().token(config["token"]).build()
    application.bot_data = {
        'db': db,
        'config': config
    }
    application.job_queue.run_repeating(check_schedules, interval=5)
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    login_handler = CommandHandler('login', login)
    application.add_handler(login_handler)

    channel_handler = CommandHandler('channel', channel)
    application.add_handler(channel_handler)

    schedule_handler = CommandHandler('schedule', schedule)
    application.add_handler(schedule_handler)

    message_handler = CommandHandler('message', message)
    application.add_handler(message_handler)
    
    application.run_polling()