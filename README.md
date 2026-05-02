# EspeonBot

A personal Discord bot that tracks habits, logs activities, times focus sessions, roasts you for skipping class, and will continue to ping you until you get tasks done.

## ✨ Features

📋 **Tracking** - Track recurring tasks with customizable reminders. Set a duration and an optional hour, and the bot will pester you when you're overdue. Snooze reminders when you need a break.

✍🏽 **Logging** - Record anything without reminders. Log haircuts, meals, showers, whatever you want to keep a history of. View and manage entries with numbered history.

😤 **Focus** - Timed focus and break sessions with stats. See how much time you've spent focusing vs taking breaks, broken down by task. If someone mentions you while you're focusing, the bot lets them know.

👻 **Skips** - Log skipped activities and get roasted for it. The bot detects lecture skips (anything with a 3-digit course number) and pulls from a separate pool of academic roasts. Add your own custom roast messages.

## 👩🏽‍💻 Using the bot

Just want to add EspeonBot to your server? Use this invite link:

[Invite EspeonBot to your server](https://discord.com/oauth2/authorize?client_id=1496774091791798352&permissions=83968&integration_type=0&scope=bot+applications.commands)

That's it 🥳

## 🔒 Privacy
EspeonBot stores task names, logs, and timestamps in a database hosted by the bot owner. The bot owner has access to the database. Please, don't track anything you wouldn't want the admin to see 😭. Self-hosting gives you full control over your own data.

## ⌨️ Commands

- `!help` to list all the commands and how to use the bot.

### 📋 Tracking
- `!track <name> <duration> [hour]` - start tracking something
- `!edit <name> <duration> [hour]` - change duration/hour (use `-` to skip a field)
- `!untrack <name>` - stop tracking and delete all entries
- `!status` - see what's overdue
- `!list` - see all your tasks
- `!snooze <name> [duration]` - delay reminders (default 8h)
- `!done <name>` - log a tracked task (resets the countdown)

### ✍🏽 Logging
- `!log <name>` - log something with no reminders
- `!history <name>` - see all entries for something
- `!delete <name> <entry_number>` - delete a specific entry

### 👻 Skips
- `!skip <name>` - log a skip and get roasted
- `!skips` - see skip counts for everything
- `!skips <name>` - see skip dates for one thing

### 🤡 Roasts
- `!addroast <message>` - add a custom roast message
- `!listroasts` - see all custom roasts
- `!editroast <number> <new message>` - edit a roast
- `!deleteroast <number>` - delete a roast

### 😤 Focus
- `!focus <label> [duration]` - start a focus session (default 25mi)
- `!break [duration]` - take a break (default 5mi)
- `!stop` - end current session early
- `!sessions` - see recent focus/break entries
- `!stats` - see focus vs break totals

### 🐌 Durations
Supports single or combined units:
- `5mi` - 5 minutes
- `3h` - 3 hours
- `7d` - 7 days
- `2w` - 2 weeks
- `6mo` - 6 months
- `1h30mi` - 1 hour 30 minutes
- `2w3d` - 2 weeks 3 days

### 🕰️ Hour
Optional 24-hour format for reminders:
- 0 = 12 AM midnight
- 9 = 9 AM
- 12 = 12 PM noon
- 14 = 2 PM
- 21 = 9 PM
- 23 = 11 PM

## 🌐 Hosting
The bot is hosted on PebbleHost and runs 24/7. If you want to run your own copy instead, follow the self-hosting instructions below.

## 🏠 Self-hosting
Self-hosting gives you your own database. Your data stays completely separate from anyone else running the bot.

### 1. 👨🏽‍🎨 Create the bot on Discord
- Go to https://discord.com/developers/applications
- Click **New Application** and give it a name
- Go to **Bot** on the left sidebar
- Click **Reset Token** and copy it - you'll need this in step 3
- Scroll down to **Privileged Gateway Intents** and enable:
  - **Message Content Intent**
  - **Server Members Intent**
- Click **Save Changes**

### 2. 💌 Invite the bot to your server
- Go to **OAuth2 -> URL Generator** on the left sidebar
- Under **Scopes**, check `bot` and `applications.commands`
- Under **Bot Permissions**, check `Send Messages`, `Read Message History`, and `Embed Links`
- Copy the generated URL at the bottom
- Open it in your browser and select which server to add the bot to

### 3. 💻 Set up the project
```bash
git clone https://github.com/yourusername/EspeonBot.git
cd EspeonBot
python -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 4. 🗝️ Add your bot token
Create a `.env` file in the project root:
```
DISCORD_TOKEN=paste_your_token_here
```
No quotes, no spaces around the `=`.

### 5. 🚀 Run the bot
```bash
python espeonbot.py
```
You should see `Bot running as YourBotName#1234` in the terminal. The bot should appear online in your server.

## ⛓️ Tests
```bash
pytest
```

## 📁 Project Structure
```
EspeonBot/
  .env
  .gitignore
  README.md
  requirements.txt
  pytest.ini
  conftest.py
  espeonbot.py
  db.py
  helpers.py
  cogs/
    __init__.py
    tracking.py
    logging_tasks.py
    skips.py
    focus.py
  tests/
    test_helpers.py
    test_db.py
    test_commands.py
```

## ⚙️ Tech Stack
- Python 🐍
- discord.py 👾
- SQLite3 🗄️
- pytest 🥧
