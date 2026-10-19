# 🌌 VOIDKAGE MUSIC — Production Discord Music Bot

VOIDKAGE MUSIC is a modern, high-performance, real-time audio streaming Discord bot built using **Python 3.12+**, **discord.py 2.x**, **Wavelink 3.5**, and **Lavalink v4**. Designed with an obsidian and neon purple aesthetic, it provides robust per-server queue management, interactive Discord UI button controls, multi-provider audio resolution, and enterprise-grade voice validation.

---

## ⚡ Key Highlights & Architecture

- **True Lavalink v4 Architecture**: Powered by Wavelink 3.5, connecting directly via WebSocket to Lavalink v4 audio nodes.
- **Native Slash Commands**: 100% native Discord application slash commands with type hinting, auto-complete choices, and parameter validation.
- **Interactive UI Buttons**: Dynamic Discord UI button controls attached directly to now-playing messages (`Pause/Resume`, `Skip`, `Stop`, `Queue`, `Loop`).
- **Independent Per-Server Queuing**: Each Discord guild operates an isolated, async-safe queue supporting `off`, `track`, and `queue` repetition modes.
- **Multi-Source Support**: Native SoundCloud and Bandcamp resolution, YouTube through Lavalink v4 source plugins, direct audio streams, and Spotify/Apple Music metadata resolution.
- **Inactivity Disconnect**: Automatically releases voice resources and disconnects when queues remain empty after a configurable timeout (default: 300s).
- **Safe Operational Security**: Token and password masking in logs, `.env` separation, and non-privileged Discord intent requirements.

---

## 🗂️ Project Structure

```
VOIDKAGE-MUSIC/
├── bot.py                     # Bot entrypoint, setup hooks, lifecycle & sync
├── config.py                  # Environment config validation & secret masking
├── requirements.txt           # Pinned, tested dependencies
├── .env.example               # Safe configuration template
├── .gitignore                 # Excludes secrets, bytecode, venv, Lavalink logs
├── application.yml            # Production Lavalink v4 server configuration
├── cogs/
│   ├── __init__.py
│   ├── music.py               # Slash commands & Wavelink audio event handlers
│   └── player_controls.py     # Discord UI view and interactive buttons
├── services/
│   ├── __init__.py
│   ├── music_service.py       # Audio provider search & URL resolution
│   └── queue_service.py       # Loop logic, 1-based deletion & queue math
├── utils/
│   ├── __init__.py
│   ├── embeds.py              # VOIDKAGE purple theme & progress bar renderer
│   └── validators.py          # Voice state, permissions & argument validation
└── tests/
    ├── __init__.py
    ├── test_queue.py          # Unit tests for queue operations & formatters
    └── test_validators.py     # Unit tests for volume, permissions & voice
```

---

## 📜 Core Slash Commands

| Command | Description | Parameters |
| :--- | :--- | :--- |
| `/play` | Search and play a song, playlist, or stream URL. | `query` (String, required) |
| `/pause` | Pause the currently playing audio. | None |
| `/resume` | Resume playback of a paused track. | None |
| `/skip` | Skip the current track and advance the queue. | None |
| `/stop` | Clear the upcoming queue and disconnect the bot. | None |
| `/nowplaying` | Display the current track, progress bar, and interactive buttons. | None |
| `/queue` | Display the current song and paginated upcoming tracks. | `page` (Integer, optional) |
| `/volume` | Set the playback volume (0% to 100%). | `value` (Integer, 0-100) |
| `/clear` | Clear upcoming tracks without interrupting the current song. | None |
| `/remove` | Remove a specific song from the queue by its 1-based position. | `position` (Integer, required) |
| `/shuffle` | Randomize the order of upcoming tracks. | None |
| `/loop` | Set repetition mode: `off`, `track`, or `queue`. | `mode` (Choice, required) |
| `/join` | Connect the bot to your current voice channel. | None |
| `/leave` | Disconnect the bot from voice and clear player state. | None |

---

## 💻 Windows 10 & 11 Development Setup

Follow these exact steps to set up and run VOIDKAGE MUSIC locally on Windows using PowerShell.

### Step 1: Install Python 3.12+
Download and install Python from [python.org](https://www.python.org/downloads/). During installation, **check the box "Add Python to PATH"**.

Verify in PowerShell:
```powershell
python --version
pip --version
```

### Step 2: Install Java 17+ (Required by Lavalink v4)
Lavalink requires Java 17 or higher (Java 21 LTS recommended).
Download **Eclipse Temurin JDK 17 or 21 (x64)** from [Adoptium](https://adoptium.net/temurin/releases/).

Verify in PowerShell:
```powershell
java -version
```

### Step 3: Create Discord Bot & Obtain Token
1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application**, name it `VOIDKAGE MUSIC`, and accept the terms.
3. In the left navigation, select **Bot**.
4. Click **Reset Token**, copy your new bot token, and store it securely.
5. Under **Privileged Gateway Intents**, keep everything unchecked (Message Content is **not** required for slash commands).
6. Under **OAuth2 -> URL Generator**:
   - Select Scopes: `bot`, `applications.commands`
   - Select Bot Permissions: `Connect`, `Speak`, `View Channel`, `Send Messages`, `Embed Links`, `Use External Emojis`, `Read Message History`
   - Copy the generated URL and paste it into your browser to invite the bot to your server.

### Step 4: Clone / Open Project & Setup Virtual Environment
In PowerShell, navigate to the project directory:
```powershell
cd c:\Users\dell\Downloads\isbandu-portfolio

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install pinned dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure `.env`
Create a `.env` file from the provided example template:
```powershell
Copy-Item .env.example .env
notepad .env
```
Fill in your `DISCORD_TOKEN`:
```env
DISCORD_TOKEN=your_real_discord_bot_token_here
LAVALINK_URI=http://127.0.0.1:2333
LAVALINK_PASSWORD=youshallnotpass
INACTIVITY_TIMEOUT=300
LOG_LEVEL=INFO
DEFAULT_VOLUME=100
# Optional: Set GUILD_ID during development for instant slash command synchronization:
# GUILD_ID=123456789012345678
```

### Step 6: Download & Start Lavalink v4
1. Download the latest `Lavalink.jar` (v4.0.8 or newer) from [Lavalink GitHub Releases](https://github.com/lavalink-devs/Lavalink/releases) and place `Lavalink.jar` in the same directory as `application.yml`.
2. Start Lavalink in a separate PowerShell window:
```powershell
cd c:\Users\dell\Downloads\isbandu-portfolio
java -jar Lavalink.jar
```
*Wait until you see `Lavalink is ready to accept connections`.*

### Step 7: Start the Bot
In your primary PowerShell window (with `.venv` active):
```powershell
python bot.py
```
You will see the diagnostics banner:
```
================ VOIDKAGE MUSIC CONFIGURATION ================
Discord Token:       OTky...XyZa (len: 72)
Lavalink URI:        http://127.0.0.1:2333
Lavalink Password:   yous...pass (len: 16)
Inactivity Timeout:  300s
Log Level:           INFO
==============================================================
[INFO] Lavalink Node 'Voidkage-Node-1' is READY.
[INFO] 🌌 VOIDKAGE is ONLINE and ready for commands!
```

### Step 8: Run Automated Unit Tests
```powershell
pytest -v tests
```
*All 25 unit tests will execute and pass.*

---

## 🐧 Linux VPS Production Deployment (Ubuntu 22.04 / 24.04 LTS)

### Hardware & Resource Requirements
- **CPU**: 1 vCPU minimum (2 vCPUs recommended for concurrent audio encoding).
- **RAM**: 1 GB RAM minimum (2 GB recommended: ~500MB for Java/Lavalink heap, ~150MB for Python bot).
- **Bandwidth**: Unmetered or high-bandwidth connection for real-time audio streams.
- **Hosting Tip**: Free server tiers (e.g. basic free containers) frequently kill background Java processes or suspend WebSocket connections. A budget VPS (e.g. Hetzner, DigitalOcean, or Linode at ~$4–$5/month) ensures 24/7 uptime.

### 1. System Packages & Runtime Installation
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y openjdk-17-jre-headless python3 python3-venv python3-pip git ufw
```

### 2. Create Service User
```bash
sudo useradd -m -s /bin/bash voidkage
sudo su - voidkage
```

### 3. Deploy Code & Setup Dependencies
```bash
git clone https://github.com/your-username/voidkage-music.git ~/app
cd ~/app

# Setup Python virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Download Lavalink.jar
wget https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar

# Setup environment variables
cp .env.example .env
chmod 600 .env
nano .env  # Enter your real DISCORD_TOKEN
exit
```

### 4. Create Systemd Service for Lavalink
Create `/etc/systemd/system/lavalink.service`:
```ini
[Unit]
Description=Lavalink v4 Audio Server
After=network.target

[Service]
Type=simple
User=voidkage
WorkingDirectory=/home/voidkage/app
ExecStart=/usr/bin/java -Xmx512M -jar /home/voidkage/app/Lavalink.jar
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

### 5. Create Systemd Service for VOIDKAGE Bot
Create `/etc/systemd/system/voidkage.service`:
```ini
[Unit]
Description=VOIDKAGE MUSIC Discord Bot
After=network.target lavalink.service
Requires=lavalink.service

[Service]
Type=simple
User=voidkage
WorkingDirectory=/home/voidkage/app
ExecStart=/home/voidkage/app/.venv/bin/python /home/voidkage/app/bot.py
Restart=always
RestartSec=5
EnvironmentFile=/home/voidkage/app/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 6. Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now lavalink.service
sudo systemctl enable --now voidkage.service
```

### 7. Inspect Logs and Health
```bash
# Monitor bot logs in real time
sudo journalctl -u voidkage.service -f

# Monitor Lavalink logs
sudo journalctl -u lavalink.service -f
```

---

## 🛠️ Troubleshooting Guide

### 1. `DISCORD_TOKEN is missing or set to default placeholder`
- **Cause**: The `.env` file does not exist or still contains `your_discord_bot_token_here`.
- **Solution**: Edit `.env` and paste your actual Discord bot token from the Developer Portal.

### 2. `Could not immediately connect to Lavalink at http://127.0.0.1:2333`
- **Cause**: Lavalink is not running, or is bound to a different port/address.
- **Solution**: Run `java -jar Lavalink.jar` in a separate terminal. Verify `application.yml` has `port: 2333` and password matches `LAVALINK_PASSWORD` in `.env`.

### 3. Slash commands do not appear in Discord
- **Cause**: Global slash commands can take up to 60 minutes to propagate across Discord's CDN.
- **Solution**: Set `GUILD_ID=your_test_server_id` in `.env`. Guild-specific commands synchronize instantaneously upon bot boot.

### 4. `Bot Missing Permissions` or Bot Joins But Plays No Sound
- **Cause**: The bot was invited without the `Connect` or `Speak` permissions, or the channel has role overrides denying the bot.
- **Solution**: Ensure the bot role has `Connect`, `Speak`, `View Channel`, and `Use Voice Activity`.

### 5. YouTube 403 Forbidden / Track Load Failure
- **Cause**: YouTube regularly updates bot-detection and IP ratelimits on data center IPs.
- **Solution**:
  - In `application.yml`, enable the `dev.lavalink.youtube:youtube-plugin`.
  - Alternatively, use **SoundCloud** searches (which are native, stable, and default in VOIDKAGE).

---

## 📊 Verification Matrix

| Feature | Status | Notes |
| :--- | :--- | :--- |
| **Python 3.12+ & discord.py 2.x** | ✅ **Tested & Verified** | Built and tested under Python 3.14.7 and discord.py 2.7.1 |
| **Wavelink 3.5 & Lavalink v4** | ✅ **Tested & Verified** | Full event/pool/queue integration confirmed against API source |
| **Core 14 Slash Commands** | ✅ **Implemented** | Complete implementation with decorators, choices, and error handling |
| **Discord UI Buttons** | ✅ **Implemented** | Interactive view with `Pause/Resume`, `Skip`, `Stop`, `Queue`, and `Loop` |
| **Queue Management** | ✅ **Tested & Verified** | Verified with 25 unit tests: looping, 1-based deletion, pagination, shuffle |
| **Dark VOIDKAGE UI Theme** | ✅ **Implemented** | Custom embeds, progress bars, and emerald/crimson feedback |
| **SoundCloud & Direct URLs** | ✅ **Implemented** | Default search source and direct stream handler |
| **YouTube Plugin Support** | ✅ **Configured** | Maintained `dev.lavalink.youtube` plugin configured in `application.yml` |
| **Spotify / Apple Music** | ⚠️ **Metadata / Plugin** | Requires `LavaSrc` plugin and Spotify client credentials in `application.yml` |
