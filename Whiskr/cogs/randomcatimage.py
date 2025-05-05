from discord.ext import commands
from discord import app_commands, ui, Interaction
import discord
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("config.env"))
CATAPIKEY = os.getenv("CATAPI")
vote_cache = {}

async def fetch_cat_image():
    headers = {"x-api-key": CATAPIKEY}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()

                # return both image URL and breed info (if available)
                image_url = data[0]["url"]
                image_id = data[0]["id"]  # image ID for voting feature

                breed_info = data[0].get("breeds", [])
                return image_url, breed_info, image_id

            else:
                error_message = await resp.text()
                raise Exception(f"Failed to fetch image (Status {resp.status}): {error_message}")


async def vote_on_image(image_id: str, vote_type: str, user_id: int):
    headers = {"x-api-key": CATAPIKEY}
    data = {
        "image_id": image_id,
        "value": 1 if vote_type == "upvote" else 0  # 1 for upvote, 0 for downvote
    }

    if image_id in vote_cache and user_id in vote_cache[image_id]:
        return False  # member has already voted

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.thecatapi.com/v1/votes", json=data, headers=headers) as resp:
            if resp.status == 201:
                if image_id not in vote_cache: # adds the user to a cache to prevent them from voting again on the same image
                    vote_cache[image_id] = set()

                vote_cache[image_id].add(user_id)
                print(f"Successfully voted {vote_type} on image ID {image_id}")
                return True
            
            else:
                error_message = await resp.text()
                raise Exception(f"Failed to vote {vote_type} (Status {resp.status}): {error_message}")


class CatView(ui.View):
    def __init__(self, user: discord.User, image_id: str):
        super().__init__(timeout=120)
        self.user = user
        self.image_id = image_id

    @ui.button(label="Randomize", style=discord.ButtonStyle.secondary, emoji="🎲")
    async def randomize(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ You can't use this button!", ephemeral=True)
            return

        try:
            new_image, breed_info, new_image_id = await fetch_cat_image()

            # if breed info is available, include it in the message
            if breed_info:
                breed_name = breed_info[0].get("name", "Unknown")
                breed_details = f"**Breed**: `{breed_name}`"

            else:
                breed_details = "No breed information available."

            # send the new cat image with breed details and buttons
            await interaction.response.edit_message(content=f"{new_image}\n{breed_details}\n-# Fetched with TheCatAPI", view=CatView(interaction.user, new_image_id))
            print(f"Successfully sent new cat image by {interaction.user.name} (ID: {interaction.user.id})!")

        except Exception as e:
            await interaction.response.send_message(f"Failed to get a new cat image 😿\n```{e}```", ephemeral=True)
            print(f"Failed to fetch image: {e}")



    @ui.button(style=discord.ButtonStyle.green, emoji="👍")
    async def upvote(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ You can't use this button!", ephemeral=True)
            return

        try:
            # call the API via function to upvote
            success = await vote_on_image(self.image_id, "upvote", interaction.user.id)

            if success:
                await interaction.response.send_message(f"Successfully upvoted this image to TheCatAPI!", ephemeral=True)
                print(f"Successfully upvoted {self.image_id} for {interaction.user.name} (ID: {interaction.user.id})!")

            else:
                await interaction.response.send_message(f"You've already voted on this image. You can only vote once!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Failed to upvote: {e}", ephemeral=True)
            print(f"Failed to upvote: {e}")


    @ui.button(style=discord.ButtonStyle.red, emoji="👎")
    async def downvote(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ You can't use this button!", ephemeral=True)
            return

        try:
            success = await vote_on_image(self.image_id, "downvote", interaction.user.id)
            if success:
                await interaction.response.send_message(f"Successfully downvoted this image to TheCatAPI!", ephemeral=True)
                print(f"Successfully downvoted {self.image_id} for {interaction.user.name} (ID: {interaction.user.id})!")

            else:
                await interaction.response.send_message(f"You've already voted on this image. You can only vote once!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Failed to downvote: {e}", ephemeral=True)
            print(f"Failed to downvote: {e}")



    @ui.button(style=discord.ButtonStyle.blurple, emoji="⭐")
    async def favorite(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ You can't use this button!", ephemeral=True)
            return

        headers = {"x-api-key": CATAPIKEY}
        data = {
            "image_id": self.image_id,
            "sub_id": str(interaction.user.id)
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.thecatapi.com/v1/favourites", json=data, headers=headers) as resp:
                if resp.status == 200 or resp.status == 201:
                    await interaction.response.send_message("⭐ Image added to your favorites!\nUse `/favorites` to view them!", ephemeral=True)
                    print(f"Successfully favorited {self.image_id} for {interaction.user.name} (ID: {interaction.user.id})!")

                else:
                    err = await resp.text()
                    await interaction.response.send_message(f"Failed to favorite: {err}", ephemeral=True)
                    print(f"Failed to favorite: {err}")


class Cat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="randomimage", description="Fetch a random cat image")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def cat(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        print(f"/cat command executed by {interaction.user} (ID: {interaction.user.id})")

        try:
            image_url, breed_info, image_id = await fetch_cat_image()

            # build cat info
            if breed_info:
                breed_name = breed_info[0].get("name", "Unknown")
                breed_details = f"**Breed**: `{breed_name}`"

            else:
                breed_details = "No breed information available."

            view = CatView(interaction.user, image_id)
            await interaction.followup.send(f"{image_url}\n{breed_details}\n-# Fetched with TheCatAPI", view=view)
            print(f"Successfully sent cat image for {interaction.user.name} (ID: {interaction.user.id})")

        except Exception as e:
            await interaction.followup.send(f"Failed to get a cat image 😿\n```{e}```")
            print(f"Failed to fetch image: {e}")


async def setup(bot):
    await bot.add_cog(Cat(bot))
