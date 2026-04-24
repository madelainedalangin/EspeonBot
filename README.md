# EspeonBot

A personal Discord bot for tracking habits, logging activities, focused work sessions, and keeping me in check.

## Features (WIP) 
- Track recurring tasks with reminders and option to snooze
- Log activities without reminders 
- Focus/break timer with stats 
- Class skip tracker (adding one liner mean punchlines bc I will need it) 

## Setup

### 1. Create the bot on Discord
- Go to https://discord.com/developers/applications
- Click **New Application** and give it a name
- Go to **Bot** on the left sidebar
- Click **Reset Token** and copy it — you'll need this in step 3
- Scroll down to **Privileged Gateway Intents** and enable **Message Content Intent**
- Click **Save Changes**

### 2. Invite the bot to your server
- Go to **OAuth2 → URL Generator** on the left sidebar
- Under **Scopes**, check `bot` and `applications.commands`
- Under **Bot Permissions**, check `Send Messages`, `Read Message History`, and `Embed Links`
- Copy the generated URL located at the very bottom of this page
- Open it in your browser and select which server to add the bot to

### 3. Set up the project
```bash
git clone https://github.com/yourusername/EspeonBot.git
cd EspeonBot
python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 4. Add your bot token
Create a `.env` file in the project root:

```python
DISCORD_TOKEN=paste_your_token_here
```
Note: please make sure there are no spaces nor quotes around `=`

### 5. Run the bot

```bash
python espeonbot.py
```
You should see `Bot running as YourBotName#1234` in the terminal. The bot should appear online in your server.

## Tests

```bash
pytest
```
