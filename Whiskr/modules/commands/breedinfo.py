from discord.ext import commands
from discord import app_commands, Embed
import discord
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("config.env"))
CATAPIKEY = os.getenv("CATAPI")

# cache for breeds
breed_cache = {}

async def fetch_breeds():  # gets every breed in thecatapi
    global breed_cache  # needed so the variable isn't local to the function
    if breed_cache:
        return breed_cache

    headers = {"x-api-key": CATAPIKEY}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/breeds", headers=headers) as resp: # send a HTTP GET request to get every breed on TheCatAPI
            if resp.status == 200: # 200 = success
                data = await resp.json() # gets the JSON response
                breed_cache = {breed["name"]: breed["id"] for breed in data}

                print("[+] Fetched list of cat breeds")
                return breed_cache # returns the breed cache
            
            else:
                error_message = await resp.text()
                raise Exception(f"[X] Failed to fetch breeds: {error_message}")


async def fetch_breed_info(breed_id: str): # fetches detailed information about a specific breed
    headers = {"x-api-key": CATAPIKEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.thecatapi.com/v1/breeds/{breed_id}", headers=headers) as resp:
            if resp.status == 200:
                print(f"[+] Fetched breed info for {breed_id}")
                return await resp.json() # returns the JSON data of the breed id
            
            else:
                error_message = await resp.text()
                raise Exception(f"Failed to fetch breed info: {error_message}")


async def fetch_cat_image(breed_id: str = None): # Fetches a cat image of the breed
    headers = {"x-api-key": CATAPIKEY}
    params = {"breed_ids": breed_id} if breed_id else {}

    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search", headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json() # returns the JSON data of the image
                breed_info = data[0].get("breeds", [])

                print(f"[+] Fetched cat image for breed {breed_id}")
                return data[0]["url"], breed_info
            
            else:
                error_message = await resp.text()
                raise Exception(f"Failed to fetch image (Status {resp.status}): {error_message}")

# --- 

class BreedInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="breedinfo", description="Get detailed information about a specific cat breed")
    @discord.app_commands.allowed_installs(guilds=True, users=True) # allows the command to be used in guilds, DMs, and private channels
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(breed="Choose a cat breed (Search specific terms if you can't find what you want)")
    async def breedinfo(self, interaction: discord.Interaction, breed: str):
        await interaction.response.defer(thinking=True)
        print(f"[+] /breedinfo executed by {interaction.user.name} (ID: {interaction.user.id})")

        breeds = await fetch_breeds()
        breed_id = breeds.get(breed)
        if not breed_id:
            await interaction.followup.send("Invalid breed selected. Please try again.")
            return

        try:
            breed_info = await fetch_breed_info(breed_id)
            breed_image_url, _ = await fetch_cat_image(breed_id)  # fetch the breed image

            breed_embed = self.get_breed_embed(breed_info, breed_image_url)
            await interaction.followup.send(embed=breed_embed)
            print(f"[+] Successfully fetched breed info for {breed} by {interaction.user.name} (ID: {interaction.user.id})!")

        except Exception as e:
            await interaction.followup.send(f"Failed to fetch breed info 😿\n```{e}```")


    def get_breed_embed(self, breed_info, breed_image_url):  # gets and returns breed details as an embed
        breed_name = breed_info.get("name", "Unknown name")
        breed_description = breed_info.get("description", "No description available")
        breed_temperament = breed_info.get("temperament", "No temperament info available")
        breed_lifespan = breed_info.get("life_span", "Unknown lifespan")
        breed_weight = breed_info.get("weight", {}).get("metric", "Unknown")

        embed = Embed(title=f"🐈 Breed Info for {breed_name}",
                      description=breed_description,
                      color=discord.Color.blue())

        embed.add_field(name="Temperament", value=breed_temperament, inline=False)
        embed.add_field(name="Life Span", value=f"{breed_lifespan} years", inline=False)
        embed.add_field(name="Weight", value=f"{breed_weight} kg", inline=False)

        if breed_image_url:  # check if an image URL is available, then set it as a thumbnail
            embed.set_image(url=breed_image_url)

        embed.set_footer(text="Data fetched from TheCatAPI")
        embed.timestamp = discord.utils.utcnow()

        return embed
    

    @breedinfo.autocomplete("breed")
    async def breed_autocomplete(self, interaction: discord.Interaction, current: str):
        breeds = await fetch_breeds()

        # filters what the user types; NOT case sensitive
        filtered_breeds = [
            app_commands.Choice(name=breed, value=breed)
            for breed in breeds
            if current.lower() in breed.lower()
        ]

        if len(filtered_breeds) == 0:
            filtered_breeds.append(app_commands.Choice(name="I couldn't find anything that matches your search.", value="no_match"))

        return filtered_breeds[:25]  # limit to 25 for Discord's API limit


async def setup(bot):
    await bot.add_cog(BreedInfo(bot))
