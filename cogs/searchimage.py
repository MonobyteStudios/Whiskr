from discord.ext import commands
from discord import app_commands, ui, Interaction
import discord
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("config.env"))
CATAPIKEY = os.getenv("CATAPI")
breed_cache = {}
vote_cache = {}

async def fetch_cat_image(breed_id: str = None): # gets a cat image of a breed
    headers = {"x-api-key": CATAPIKEY}
    params = {"breed_ids": breed_id} if breed_id else {}

    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search", headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                breed_info = data[0].get("breeds", [])
                return data[0]["url"], breed_info, data[0]["id"]
            
            else:
                raise Exception(f"Failed to fetch image: {await resp.text()}")

async def fetch_breeds(): # gets every breed from thecatapi
    global breed_cache
    if breed_cache:
        return breed_cache

    headers = {"x-api-key": CATAPIKEY}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/breeds", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                breed_cache = {breed["name"]: breed["id"] for breed in data}
                return breed_cache
            else:
                raise Exception(f"Failed to fetch breeds: {await resp.text()}")

async def vote_on_image(image_id: str, vote_type: str, user_id: int): # implementation for upvoting, downvoting
    headers = {"x-api-key": CATAPIKEY}
    data = {
        "image_id": image_id,
        "value": 1 if vote_type == "upvote" else 0
    }

    if image_id in vote_cache and user_id in vote_cache[image_id]:
        return False

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.thecatapi.com/v1/votes", json=data, headers=headers) as resp:
            if resp.status == 201:
                vote_cache.setdefault(image_id, set()).add(user_id)
                return True
            
            else:
                raise Exception(await resp.text())
            

class Options(ui.View):
    def __init__(self, user: discord.User, breed_id: str, image_id: str, breed_info: str):
        super().__init__(timeout=120)
        self.user = user
        self.breed_id = breed_id
        self.image_id = image_id
        self.breed_info = breed_info

    @ui.button(label="🎲 Randomize", style=discord.ButtonStyle.secondary)
    async def randomize(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ This isn't your session!", ephemeral=True)

        try:
            new_image, new_info, new_id = await fetch_cat_image(self.breed_id)
            breed_name = new_info[0]["name"] if new_info else "Unknown"

            view = Options(self.user, self.breed_id, new_id, breed_name)
            await interaction.response.edit_message(content=f"{new_image}\n**Breed**: {breed_name}\n-# Fetched with TheCatAPI", view=view)

        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)


    @ui.button(emoji="👍", style=discord.ButtonStyle.green)
    async def upvote(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ You can't vote on this!", ephemeral=True)

        try:
            if await vote_on_image(self.image_id, "upvote", interaction.user.id):
                await interaction.response.send_message("Successfully upvoted this image!", ephemeral=True)
                print(f"Successfully upvoted {self.image_id} for {interaction.user.name} (ID: {interaction.user.id})!")

            else:
                await interaction.response.send_message("You've already voted on this image.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Upvote failed: {e}", ephemeral=True)
            print(f"Failed to upvote: {e}")


    @ui.button(emoji="👎", style=discord.ButtonStyle.red)
    async def downvote(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ You can't vote on this!", ephemeral=True)

        try:
            if await vote_on_image(self.image_id, "downvote", interaction.user.id):
                await interaction.response.send_message("Successfully downvoted this image!", ephemeral=True)
                print(f"Successfully downvoted {self.image_id} for {interaction.user.name} (ID: {interaction.user.id})!")

            else:
                await interaction.response.send_message("You've already voted on this image.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Downvote failed: {e}", ephemeral=True)
            print(f"Failed to downvote: {e}")

    @ui.button(emoji="⭐", style=discord.ButtonStyle.blurple)
    async def favorite(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ You can't interact with this!", ephemeral=True)

        headers = {"x-api-key": CATAPIKEY}
        data = {
            "image_id": self.image_id,
            "sub_id": str(interaction.user.id)
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.thecatapi.com/v1/favourites", json=data, headers=headers) as resp:
                if resp.status in (200, 201):
                    await interaction.response.send_message("⭐ Image added to your favorites!\nUse `/favorites` to view them!", ephemeral=True)
                    print(f"Successfully favorited {self.image_id} for {interaction.user.name} (ID: {interaction.user.id}!)")

                else:
                    await interaction.response.send_message(f"Favorite failed: {await resp.text()}", ephemeral=True)


class BreedCat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="searchimage", description="Fetch a cat image of a specific breed")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(breed="Choose a cat breed (Search specific terms if you can't find what you want)")
    async def searchimage(self, interaction: discord.Interaction, breed: str):
        await interaction.response.defer(thinking=True)

        breeds = await fetch_breeds()
        breed_id = breeds.get(breed)

        if not breed_id:
            await interaction.followup.send("Invalid breed selected. Please try again.")
            return

        try:
            image_url, breed_info, image_id = await fetch_cat_image(breed_id=breed_id)
            breed_details = self.get_breed_details(breed_info)

            view = Options(interaction.user, breed_id=breed_id, image_id=image_id, breed_info=breed_info)
            await interaction.followup.send(f"{image_url}\n{breed_details}\n-# Fetched with TheCatAPI", view=view)
            print(f"Successfully sent {breed} breed image by {interaction.user.name} (ID: {interaction.user.id})!")

        except Exception as e:
            await interaction.followup.send(f"Failed to get a cat image 😿\n```{e}```")

    def get_breed_details(self, breed_info):
        if breed_info:
            breed_name = breed_info[0].get("name", "Unknown")
            return f"**Breed**: {breed_name}"
        
        else:
            return "No breed information available."

    @searchimage.autocomplete("breed")
    async def breed_autocomplete(self, interaction: discord.Interaction, current: str):
        breeds = await fetch_breeds()

        filtered_breeds = [
            app_commands.Choice(name=breed, value=breed)
            for breed in breeds
            if current.lower() in breed.lower()
        ]
        
        if not filtered_breeds:
            filtered_breeds.append(app_commands.Choice(
                name="I couldn't find anything that matches your search.",
                value="no_match"
            ))

        return filtered_breeds[:25]

async def setup(bot):
    await bot.add_cog(BreedCat(bot))