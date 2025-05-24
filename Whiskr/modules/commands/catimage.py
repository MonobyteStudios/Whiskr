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
category_cache = {}

async def fetch_cat_image(breed_id: str = None, category_id: int = None):
    headers = {"x-api-key": CATAPIKEY}
    params = {}

    # if specified, add them to params
    if breed_id:
        params["breed_ids"] = breed_id
    if category_id:
        params["category_ids"] = category_id

    async with aiohttp.ClientSession() as session: # HTTP GET
        async with session.get("https://api.thecatapi.com/v1/images/search", headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json() # gets JSON response
                
                if not data:
                    raise Exception("No images match your search")
                print(f"[+] Successfully retrieved cat image")

                breed_info = data[0].get("breeds", [])
                return data[0]["url"], breed_info, data[0]["id"]
            
            else:
                raise Exception(f"[X] Failed to fetch image: {await resp.text()}")

async def fetch_breeds(): # gets every breed from thecatapi
    global breed_cache
    if breed_cache:
        return breed_cache

    headers = {"x-api-key": CATAPIKEY}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/breeds", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                breed_cache = {breed["name"]: breed["id"] for breed in data} # adds every breed to breed_cache
                print("[+] Successfully fetched breeds")

                return breed_cache # returns the data
            else:
                print("")
                raise Exception(await resp.text())

async def fetch_categories(): # gets every category from the API
    global category_cache
    if category_cache:
        return category_cache

    headers = {"x-api-key": CATAPIKEY}
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/categories", headers=headers) as resp: # HTTP GET
            if resp.status == 200:
                data = await resp.json()
                category_cache = {cat["name"]: cat["id"] for cat in data} # adds every category with its ID to the cache
                print("[+] Successfully fetched categories")

                return category_cache # returns the data
            
            else:
                raise Exception(await resp.text())
            

async def vote_on_image(image_id: str, vote_type: str, user_id: int): # implementation for upvoting, downvoting
    headers = {"x-api-key": CATAPIKEY}
    data = {
        "image_id": image_id,
        "value": 1 if vote_type == "upvote" else 0 # 1 = upvote, 0 = downvote
    }
    if image_id in vote_cache and user_id in vote_cache[image_id]:
        return False # member cant vote again

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.thecatapi.com/v1/votes", json=data, headers=headers) as resp:
            if resp.status == 201: # successfully voted on image ID
                vote_cache.setdefault(image_id, set()).add(user_id) # adds the member to a cache

                return True
            
            else:
                raise Exception(await resp.text())
            

class Options(ui.View): # buttons
    def __init__(self, user: discord.User, breed_id: str, image_id: str, breed_info: str, category_id=None):
        super().__init__(timeout=120)
        # self.[x] is used on buttons, its imported from the arguments above ^^^^
        self.user = user
        self.breed_id = breed_id
        self.category_id = category_id
        self.image_id = image_id

    @ui.button(label="🎲 Randomize", style=discord.ButtonStyle.secondary)
    async def randomize(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ You can't interact with this!", ephemeral=True)

        try:
            image, info, id = await fetch_cat_image(breed_id=self.breed_id, category_id=self.category_id)
            breed_name = info[0]["name"] if info else "Not available"

            view = Options(self.user, self.breed_id, id, info, self.category_id)
            await interaction.response.edit_message(content=f"{image}\n**Breed**: {breed_name}\n-# Fetched with TheCatAPI", view=view)
            print(f"[+] Successfully randomized cat image for {interaction.user.name}")

        except Exception as e:
            print(f"[X] Failed to send new cat image: {e}")
            await interaction.response.send_message(f"I failed to find a new image: {e}", ephemeral=True)



    @ui.button(emoji="👍", style=discord.ButtonStyle.secondary)
    async def upvote(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ You can't interact with this!", ephemeral=True)

        try:
            if await vote_on_image(self.image_id, "upvote", interaction.user.id):
                await interaction.response.send_message("Successfully upvoted this image!", ephemeral=True)
                print(f"[+] Successfully upvoted {self.image_id} for {interaction.user.name} (ID: {interaction.user.id})!")

            else:
                await interaction.response.send_message("You've already voted on this image.", ephemeral=True)
                print(f'[-] {interaction.user.name} has already voted on this image')

        except Exception as e:
            await interaction.response.send_message(f"I failed to upvote this image: {e}", ephemeral=True)
            print(f"[X] Failed to upvote: {e}")


    @ui.button(emoji="👎", style=discord.ButtonStyle.secondary)
    async def downvote(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ You can't interact with this!", ephemeral=True)

        try:
            if await vote_on_image(self.image_id, "downvote", interaction.user.id):
                await interaction.response.send_message("Successfully downvoted this image!", ephemeral=True)
                print(f"[+] Successfully downvoted {self.image_id} for {interaction.user.name} (ID: {interaction.user.id})!")

            else:
                await interaction.response.send_message("You've already voted on this image.", ephemeral=True)
                print(f'[-] {interaction.user.name} has already voted on this image')

        except Exception as e:
            await interaction.response.send_message(f"I failed to downvote this image: {e}", ephemeral=True)
            print(f"[X] Failed to downvote: {e}")


    @ui.button(emoji="⭐", style=discord.ButtonStyle.secondary)
    async def favorite(self, interaction: Interaction, button: ui.Button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ You can't interact with this!", ephemeral=True)

        headers = {"x-api-key": CATAPIKEY}
        data = {
            "image_id": self.image_id,
            "sub_id": str(interaction.user.id)
        }

        async with aiohttp.ClientSession() as session: # create a POST request to favorite
            async with session.post("https://api.thecatapi.com/v1/favourites", json=data, headers=headers) as resp:
                if resp.status in (200, 201):
                    await interaction.response.send_message("⭐ Image added to your favorites!\nUse `/favorites` to view them!", ephemeral=True)
                    print(f"[+] Successfully favorited {self.image_id} for {interaction.user.name} (ID: {interaction.user.id})")

                else:
                    await interaction.response.send_message(f"Favoriting ID {self.image_id} failed: {await resp.text()}", ephemeral=True)
                    print(f"[X] Favoriting {self.image_id} failed: {await resp.text()}")


async def sort_selection(name: str, value: str, fetch, interaction: discord.Interaction):
    if value and value != "no_match":
        options = await fetch() # provided fetch function
        result = options.get(value) # get the value from the fetch

        if not result: # if the result is not found in the api
            await interaction.followup.send(f"Invalid {name} selected. Please try again.")
            print(f"[-] Specified '{name}' does not exist")
            return None
        
        return result # if everything passes, return the result
    
    return None

class BreedCat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="catimage", description="Fetch a cat image")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(
        breed="Choose a cat breed (Search specific terms if you can't find what you want)",
        category="Select a category to sort images"
    )
    async def catimage(self, interaction: discord.Interaction, breed: str = None, category: str = None):
        await interaction.response.defer(thinking=True)

        breed_id = await sort_selection("breed", breed, fetch_breeds, interaction)
        category_id = await sort_selection("category", category, fetch_categories, interaction)
        
        try:
            image_url, breed_info, image_id = await fetch_cat_image(breed_id=breed_id, category_id=category_id) # fetches an image with the details
            breed_details = self.get_breed_details(breed_info) # you know what it does

            view = Options(interaction.user, breed_id=breed_id, image_id=image_id, breed_info=breed_info, category_id=category_id)
            await interaction.followup.send(f"{image_url}\n{breed_details}\n-# Fetched with TheCatAPI", view=view)
            print(f"[+] Sent image by {interaction.user.name} with breed {breed} and category {category}!")

        except Exception as e:
            await interaction.followup.send(f"Failed to fetch a cat image\n```{e}```")
            print(f"[X] Failed to fetch image on /searchimage: {e}")


    def get_breed_details(self, breed_info):
        if breed_info:
            breed_name = breed_info[0].get("name", "Not available")
            return f"**Breed**: {breed_name}"
        
        else:
            return "No breed information available."

    # auto completes
    @catimage.autocomplete("breed")
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
    
    @catimage.autocomplete("category")
    async def category_autocomplete(self, interaction: discord.Interaction, current: str):
        categories = await fetch_categories()

        filtered_categories = [
            app_commands.Choice(name=category, value=category)
            for category in categories
            if current.lower() in category.lower()
        ]
        
        if not filtered_categories:
            filtered_categories.append(app_commands.Choice(
                name="I couldn't find anything that matches your search.",
                value="no_match"
            ))

        return filtered_categories[:25]

async def setup(bot):
    await bot.add_cog(BreedCat(bot))