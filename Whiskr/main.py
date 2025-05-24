import os
import discord
from discord.ext import commands
import aiohttp
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(
    command_prefix="!", 
    intents=intents
)

load_dotenv(dotenv_path=os.path.join("config.env"))
CATAPIKEY = os.getenv("CATAPI")


async def validate_key():
    if not CATAPIKEY:
        print("AUTHENTICATION FAILED: TheCatAPI variable in config.env is not defined.")
        raise SystemExit(1)

    headers = {"x-api-key": CATAPIKEY}
    url = "https://api.thecatapi.com/v1/favourites" # favorites requires a API key

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status in (401, 403):
                print("AUTHENTICATION FAILED: Invalid TheCatAPI key: API returned 401/403.")
                raise SystemExit(1)

            if resp.status != 200:
                print(f"AUTHENTICATION FAILED: Unexpected status code while validating key: {resp.status}")
                raise SystemExit(1)


@client.event
async def on_ready():
    await validate_key()
    print("[+] Successfully validated TheCatAPI key!")

    print("[-] Loading extensions...")

    for root, _, files in os.walk("./modules"):
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("_"):
                relative_path = os.path.relpath(os.path.join(root, filename), ".")
                extension = relative_path.replace(os.sep, ".")[:-3]  # removes the .py so it can load
                
                try:
                    await client.load_extension(extension)
                    print(f"[+] Loaded extension: {extension}")

                except Exception as e:
                    print(f"[X] Failed to load extension {extension}: {e}")

    print(f"[+] Successfully logged in as {client.user}!")
    print("[-] Syncing slash commands...")

    try:
        synced = await client.tree.sync()
        print(f"[+] Successfully synced {len(synced)} slash commands! Refresh Discord if you don't see them.")

    except Exception as e:
        print(f"[X] An error occurred while syncing slash commands: {e}")


load_dotenv(dotenv_path=os.path.join("config.env"))
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
