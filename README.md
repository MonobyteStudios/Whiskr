# Whiskr
A purr-fectly crafted Discord bot that brings you random cat pictures, breed info, and favorites — powered by TheCatAPI. Whiskr is fully open-sourced so that you can customize it to your liking.
> Developed by As2Bax (@vqel on Discord), created with discord.py 2.5.2

## Features
- 🐈 Randomized cat images - `/randomimage`
- 🔎 View cat images based on breed - `/searchimage`
- ❤️ Favorite your loved cat pictures — and view yours or others with `/favorites`
- 📰 View interesting info about cat breeds - `/breedinfo`
- 🎨 Whiskr is fully customizable; change things up, make it yours!
- 📨 User installs are supported along with guild installations
  
## Images
![The /randomimage command](https://r2.e-z.host/aa2b4cc6-0670-4139-abd2-29af34e8b12e/qeox9145.png)
![The /favorites command](https://r2.e-z.host/aa2b4cc6-0670-4139-abd2-29af34e8b12e/3kyx5k6k.png)
![The /breedinfo command](https://r2.e-z.host/aa2b4cc6-0670-4139-abd2-29af34e8b12e/72jklbjj.png)

## Installation Instructions
1. Create your Discord application (if you haven't: https://discord.com/developers/applications)
   - In your Discord application, head to the `Installation` tab and scroll down to `Guild Install`. Click `Scopes`, followed by `bot`. Another dropdown will show with permissions. Select `Send Messages` and `Attach Files` to ensure full bot functionality.
     
   - User installs are supported; if you want to use that, make sure you keep `User Install` enabled in `Installation Contexts`.
     
   - Make sure you have `Message Intents` enabled on the `Bot` page


2. Install Visual Studio Code https://code.visualstudio.com/download (Highly recommended)
   > Windows, Linux, and macOS are supported
   
3. When opened, head to `File > Open Folder`. Select '`Whiskr`' inside the extracted `codebase.zip`
   > Make sure to download `codebase.zip` - this contains everything you need to run the bot

4. Once you've opened the `Whiskr` folder inside `codebase` in VSC, fill in `config.env` with:
   - Your Discord bot token (Can be found in the `Bot` tab in your application)
   - Your TheCatAPI key (Get it here: https://thecatapi.com)

5. Head to `View > Terminal` on the top left. This will open a terminal on the bottom with a path to the folder you opened. If you set this up correctly, it should eventually lead to the `Whiskr` folder. **NOT** `codebase`.
6. Run this in the terminal box:
   ```
   pip install -r requirements.txt
   ```
   This automatically installs every package in requirements.txt
   > Make sure you also have Python installed: https://www.python.org/

7. Select `main.py` on the VSC explorer. You should see a play button on the top left. Click that. If you set up everything correctly, the bot should start without problems.
   > You can always make other ways to start this bot; as long as it starts main.py, everything will work correctly.

Have fun! You're all set up 😺

