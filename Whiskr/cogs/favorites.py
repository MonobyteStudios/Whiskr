import discord
from discord import app_commands, Interaction, ui
from discord.ext import commands
import aiohttp
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=os.path.join("config.env"))
CATAPIKEY = os.getenv("CATAPI")

class FavoritesView(ui.View):
    def __init__(self, user: discord.User, owner: discord.User, images: list):
        super().__init__(timeout=120)
        self.user = user      # who is interacting with the ui
        self.owner = owner    # who owns the favorites being shown

        self.images = images
        self.index = 0
        self.message = None

    def format_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{self.owner.name}'s Favorites",
            description=f"`Image {self.index + 1} of {len(self.images)}`",
            color=discord.Color.orange()
        )
        embed.timestamp = discord.utils.utcnow()
        embed.set_image(url=self.images[self.index]["image"]["url"])
        return embed

    

    @ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: Interaction, button: ui.Button):
        if self.index > 0:
            self.index -= 1
            await interaction.response.edit_message(embed=self.format_embed(), view=self)
            
        else:
            await interaction.response.defer()
        print("Successfully went to previous favorite!")


    @ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: Interaction, button: ui.Button):
        if self.index < len(self.images) - 1:
            self.index += 1
            await interaction.response.edit_message(embed=self.format_embed(), view=self)

        else:
            await interaction.response.defer()
        print("Successfully went to next favorite!")


    @ui.button(label="🗑️ Delete Favorite", style=discord.ButtonStyle.danger)
    async def delete_favorite(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.owner.id:
            await interaction.response.send_message("❌ You can't delete someone else's favorite.", ephemeral=True)
            return

        favorite_id = self.images[self.index]["id"]

        headers = {"x-api-key": CATAPIKEY}
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"https://api.thecatapi.com/v1/favourites/{favorite_id}", headers=headers) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    await interaction.response.send_message(f"Failed to delete favorite:\n```{error}```", ephemeral=True)
                    return

        del self.images[self.index]

        if not self.images:
            await interaction.response.edit_message(content="You haven't favorited any cats yet!", embed=None, view=None)
            return

        if self.index >= len(self.images):
            self.index = len(self.images) - 1

        await interaction.response.edit_message(embed=self.format_embed(), view=self)
        print("Successfully deleted favorite!")

class Favorites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="favorites", description="View your favorite cat images")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def favorites(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer(thinking=True)
        print(f"/favorites executed by {interaction.user.name} (ID: {interaction.user.id})!")

        owner = member or interaction.user
        value = owner.id

        headers = {"x-api-key": CATAPIKEY}
        params = {
            "sub_id": str(value),
            "limit": 20
        }

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/favourites", params=params, headers=headers) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    await interaction.followup.send(f"Failed to fetch favorites:\n```{error}```")
                    return

                data = await resp.json()
                if not data:
                    await interaction.followup.send(f"{owner.name} hasn't favorited any cats yet!")
                    return

                view = FavoritesView(user=interaction.user, owner=owner, images=data)
                embed = view.format_embed()

                view.message = await interaction.followup.send(embed=embed, view=view)
                print(f"Successfully sent /favorites response for {owner.id}")

async def setup(bot):
    await bot.add_cog(Favorites(bot))
