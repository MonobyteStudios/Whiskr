import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(
    command_prefix="!", 
    intents=intents
)

@client.event
async def on_ready():
    print("Loading extensions...")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            try:
                extension = f"cogs.{filename[:-3]}"
                await client.load_extension(extension)
                print(f"Loaded extension: {extension}")

            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")

    print(f"Successfully logged in as {client.user}!")

    print("Syncing slash commands..")
    try:
        synced = await client.tree.sync()
        print(f"Successfully synced {len(synced)} slash commands!")

    except Exception as e:
        print(f"An error has occured while attempting to sync slash commands: **{e}**")


load_dotenv(dotenv_path=os.path.join("config.env"))
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
