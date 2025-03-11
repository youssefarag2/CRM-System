import discord
import asyncio
from threading import Thread
from django.conf import settings
from queue import Queue, Empty

# Use the token from settings
# TOKEN = settings.DISCORD_TOKEN

intents = discord.Intents.default()
intents.messages = True

bot = discord.Client(intents=intents)

message_queue = Queue()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')  # Confirm the bot is logged in

async def send_discord_message(user_id, message_content):
    try:
        #print(f"Attempting to send message to user ID {user_id}")
        user = await bot.fetch_user(user_id)
        await user.send(message_content)
        #print(f"Sent a private message to {user.name}#{user.discriminator}")
    except discord.NotFound:
        print(f"User with ID {user_id} not found.")
    except discord.Forbidden:
        print(f"Sending a message to user {user_id} is not allowed.")
    except Exception as e:
        print(f"An error occurred: {e}")

async def message_dispatcher():
    while True:
        try:
            user_id, message_content = message_queue.get_nowait()
            await send_discord_message(user_id, message_content)
        except Empty:
            await asyncio.sleep(1)

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(bot.start(TOKEN))
    loop.create_task(message_dispatcher())
    loop.run_forever()

def start_bot_in_thread():
    thread = Thread(target=run_bot)
    thread.start()

def queue_message(user_id, message_content):
    message_queue.put((user_id, message_content))