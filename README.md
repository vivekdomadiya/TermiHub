# TermiHub

A personal Telegram Control Center running on your Android phone via Termux.
Send commands to your phone over Telegram — no open ports, no VPN required.

```
You ──► Telegram servers ──► Termux bot ──► Android/local services ──► reply
```

---

## Project structure

```
termihub/
├── bot.py              # Entry point — wires Application + handlers
├── config.py           # Reads config from environment variables
├── auth.py             # @restricted decorator — whitelist enforcement
├── handlers/
│   └── phone.py        # Phase 1: /battery /storage /ram /temperature /uptime /ip /wifi
├── requirements.txt    # python-telegram-bot v21 (async API)
├── setup.sh            # One-time Termux setup
├── start.sh            # Launches the bot (sources ~/.termihub.env first)
└── .env.example        # Template for your secrets
```

---

## Setup (do this once)

### Step 1 — Create a Telegram bot

1. Open Telegram → search **@BotFather** → `/newbot`
2. Follow the prompts. Copy the token it gives you (looks like `7123456789:AAF…`)

### Step 2 — Find your Telegram user ID

1. Message **@userinfobot** on Telegram
2. It replies with your numeric user ID (e.g. `123456789`)

### Step 3 — Copy the project to your phone

Option A — clone with git (if git is installed in Termux):
```bash
pkg install git
git clone https://github.com/yourname/termihub.git ~/termihub
```

Option B — copy the folder manually via USB / file manager.

### Step 4 — Run setup

```bash
cd ~/termihub
bash setup.sh
```

This installs: `python`, `iproute2`, `termux-api` via `pkg`, creates a Python
virtual environment, installs `python-telegram-bot`, and copies `.env.example`
to `~/.termihub.env`.

### Step 5 — Fill in your credentials

```bash
nano ~/.termihub.env
```

Set:
```
TERMIHUB_BOT_TOKEN=7123456789:AAF…        # from BotFather
TERMIHUB_ALLOWED_IDS=123456789             # your user ID from @userinfobot
```

### Step 6 — Install the Termux:API companion app

The `/battery`, `/wifi`, and `/temperature` commands use `termux-*` CLI tools
that are provided by the **Termux:API** Android app.

Install it from **F-Droid** (not the Play Store — the Play Store version is outdated):
https://f-droid.org/en/packages/com.termux.api/

After installing, grant the app the permissions it asks for (battery, location/Wi-Fi).

### Step 7 — Start the bot

```bash
cd ~/termihub
bash start.sh
```

You should see:
```
TermiHub started. Allowed user IDs: {123456789}
Starting polling...
```

Open Telegram, send `/start` to your bot, and you'll see the command menu.

---

## Available commands (Phase 1)

| Command | What it does | Requires |
|---|---|---|
| `/battery` | Charge %, status, health, temp | termux-api |
| `/storage` | Free / total internal storage | — |
| `/ram` | Used / available RAM | — |
| `/temperature` | Battery temp + sysfs thermal zones | termux-api (primary) |
| `/uptime` | Time since last reboot | — |
| `/ip` | Local Wi-Fi IP address | iproute2 |
| `/wifi` | SSID, signal strength, frequency | termux-api |

---

## Security model

- **Whitelist only.** Every handler is wrapped with the `@restricted` decorator
  ([`auth.py`](auth.py)). Any message from a user ID not in `ALLOWED_USER_IDS`
  is silently dropped — the bot does not reveal its existence.
- **No arbitrary shell execution.** Each command maps to exactly one hard-coded
  shell string. User-supplied text is never interpolated into a command.
- **Token in env, not in code.** `BOT_TOKEN` is read from `~/.termihub.env`
  at startup. The file lives outside the project directory so it is never
  accidentally committed.

---

## Keeping the bot running

To run the bot in the background in Termux, use `nohup` or Termux's built-in
session management:

```bash
# Option A — nohup (survives closing the Termux window)
nohup bash start.sh > ~/termihub.log 2>&1 &
echo "PID: $!"

# Option B — open a second Termux session (swipe right in Termux) and leave it running
```

To stop it:
```bash
pkill -f bot.py
```

---

## Environment variables reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `TERMIHUB_BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather |
| `TERMIHUB_ALLOWED_IDS` | ✅ | — | Comma-separated numeric user IDs |
| `TERMIHUB_CMD_TIMEOUT` | ❌ | `10` | Seconds before a shell command is killed |
| `TERMIHUB_BOT_NAME` | ❌ | `TermiHub` | Friendly name shown in messages |

---

## Roadmap

- **Phase 2 — AI:** local Ollama integration, `/ai` command, log/file analysis
- **Phase 3 — Expense Tracker:** `250 petrol`, monthly summaries, SQLite storage
- Future: Jellyfin control, Docker status, scheduled jobs, GitHub automation
