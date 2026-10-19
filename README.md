# 🎧 Void Vibe — Discord Music Bot

> **🎧 Your soundtrack, your server.**  
> *Play music, manage queues, and enjoy your favorite tracks with Void Vibe.*

Void Vibe is a modern, high-performance, real-time audio streaming Discord bot built using **Python 3.12+**, **discord.py 2.x**, **Wavelink 3.5**, and **Lavalink v4**. Designed with an obsidian black and deep neon purple aesthetic, Void Vibe delivers independent per-server queues, interactive Discord UI button controls, multi-provider audio resolution, and enterprise-grade voice validation.

---

## ⚡ Key Highlights & Features

- **True Lavalink v4 Architecture**: Powered by Wavelink 3.5, connecting via WebSocket to Lavalink v4 audio nodes with low latency and high-throughput audio encoding.
- **Native Slash Commands**: 14 100% native Discord application slash commands with type hinting, auto-complete choices, and parameter validation.
- **Interactive Discord UI Buttons**: Dynamic Discord UI button controls attached directly to `/nowplaying` and `/play` embeds (`Pause/Resume`, `Skip`, `Stop`, `Queue`, `Loop`).
- **Independent Per-Server Queuing**: Each Discord guild operates an isolated, async-safe queue supporting `off`, `track`, and `queue` repetition modes.
- **Multi-Source Support**: Native SoundCloud and Bandcamp resolution, YouTube through Lavalink v4 source plugins, direct audio streams, and Spotify/Apple Music metadata resolution.
- **Inactivity Disconnect**: Automatically releases voice resources and disconnects when queues remain empty after a configurable timeout (default: 300s).
- **Abandoned Voice Detection**: Automatically leaves and cleans up state when all human listeners leave the voice channel.
- **Safe Operational Security**: Token and password masking in logs, `.env` separation, and non-privileged Discord intent requirements.

---

## 🗂️ Project Structure

```
Void Vibe/
├── bot.py                     # Bot entrypoint, lifecycle hooks, presence & sync
├── config.py                  # Environment config validation & secret masking
├── requirements.txt           # Pinned, tested dependencies
├── .env.example               # Safe configuration template with placeholders
├── .env                       # Local secrets (ignored by Git)
├── .gitignore                 # Excludes secrets, bytecode, venv, Lavalink logs
├── application.yml            # Production Lavalink v4 server configuration
├── start-lavalink.bat         # Windows one-click Lavalink startup script
├── start-bot.bat              # Windows one-click bot startup script
├── cogs/
│   ├── __init__.py
│   ├── music.py               # 14 slash commands & Wavelink audio event handlers
│   └── player_controls.py     # Discord UI view and interactive buttons
├── services/
│   ├── __init__.py
│   ├── music_service.py       # Audio provider search & URL resolution
│   └── queue_service.py       # Loop logic, 1-based deletion & queue math
├── utils/
│   ├── __init__.py
│   ├── embeds.py              # Void Vibe dark purple theme & progress bar renderer
│   └── validators.py          # Voice state, permissions & argument validation
└── tests/
    ├── __init__.py
    ├── test_queue.py          # Unit tests for queue operations & formatters
    └── test_validators.py     # Unit tests for volume, permissions & voice
```

---

## 📜 Supported Slash Commands

| Command | Description | Parameters |
| :--- | :--- | :--- |
| `/play` | Search and play a song, playlist, or stream URL. | `query` (String, required) |
| `/pause` | Pause currently playing audio. | None |
| `/resume` | Resume playback of a paused track. | None |
| `/skip` | Skip the current track and advance the queue. | None |
| `/stop` | Clear the upcoming queue and disconnect the bot. | None |
| `/nowplaying` | Display the current track, progress bar, and interactive buttons. | None |
| `/queue` | Display the current song and paginated upcoming tracks. | `page` (Integer, optional, default: 1) |
| `/volume` | Set playback volume (0% to 100%). | `value` (Integer, 0-100, required) |
| `/clear` | Clear upcoming tracks without interrupting the current song. | None |
| `/remove` | Remove a specific song from the queue by its 1-based position. | `position` (Integer, required) |
| `/shuffle` | Randomize the order of upcoming tracks. | None |
| `/loop` | Set repetition mode: `off`, `track`, or `queue`. | `mode` (Choice, required) |
| `/join` | Connect the bot to your current voice channel. | None |
| `/leave` | Disconnect the bot from voice and clean up player state. | None |

---

## 💻 Windows 10 & 11 Local Development Workflow

Follow these steps to set up and run Void Vibe locally on Windows using PowerShell or Command Prompt.

### Prerequisites
1. **Python 3.12+** (Python 3.12, 3.13, or 3.14).  
   Verify with `python --version` and ensure Python is added to PATH.
2. **Java 17+ or Java 21 LTS** (Required by Lavalink v4).  
   Verify with `java -version`. Download [Eclipse Temurin JDK 21](https://adoptium.net/).
3. **Lavalink.jar** (v4.0.8+).

### Step 1: Open Terminal in Project Directory
Open VS Code in `C:\Users\dell\Downloads\isbandu-portfolio` and open an integrated terminal (`Ctrl + ~`).

### Step 2: Virtual Environment & Dependencies
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install / update requirements
python -m pip install -r requirements.txt
```

### Step 3: Configure `.env`
Ensure you have a `.env` file configured in the project root:
```env
DISCORD_TOKEN=your_actual_discord_bot_token
LAVALINK_URI=http://127.0.0.1:2333
LAVALINK_PASSWORD=change_this_password
INACTIVITY_TIMEOUT=300
LOG_LEVEL=INFO
DEFAULT_VOLUME=100

# Optional: Instant slash command registration in a test server during development
# GUILD_ID=123456789012345678
```

### Step 4: Start Lavalink Server
In **Terminal 1** (or double-click `start-lavalink.bat`):
```powershell
java -jar .\Lavalink.jar
```
*Wait until the console displays: `Lavalink is ready to accept connections.` on port 2333.*

### Step 5: Start Void Vibe Bot
In **Terminal 2** (or double-click `start-bot.bat`):
```powershell
.\.venv\Scripts\python.exe bot.py
```
You will see the startup banner:
```
[INFO] ================ Void Vibe CONFIGURATION ================
[INFO] Discord Token:       MTU2...EvdU (len: 72)
[INFO] Lavalink URI:        http://127.0.0.1:2333
[INFO] Inactivity Timeout:  300s
[INFO] =========================================================
[INFO] Connecting to Lavalink node at http://127.0.0.1:2333...
[INFO] Synchronized 14 global slash commands with Discord.
[INFO] Lavalink Node 'VoidVibe-Node-1' is READY.
[INFO] 🎧 Void Vibe is ONLINE and ready for commands!
[INFO] Tagline: 🎧 Your soundtrack, your server.
```

> [!NOTE]
> During local development, both the Lavalink server and the Python bot must remain running in their respective windows. Closing either window stops playback.

---

## 🤖 Discord Developer Portal Setup

Follow these exact steps to register and invite Void Vibe:

1. Open the [Discord Developer Portal](https://discord.com/developers/applications).
2. Select your application or click **New Application** and name it **Void Vibe**.
3. Under **General Information**:
   - Set Description: `Play music, manage queues, and enjoy your favorite tracks with Void Vibe.`
   - Set Tagline in About Me: `🎧 Your soundtrack, your server.`
4. In the left sidebar, navigate to **Bot**:
   - Set Bot Username to `Void Vibe`.
   - Click **Reset Token**, copy your new token, and place it in `.env` under `DISCORD_TOKEN`.
   - **Privileged Gateway Intents**: Keep all privileged intents (Presence Intent, Server Members Intent, Message Content Intent) **unchecked**. Void Vibe uses 100% native slash commands and does not require message reading.
5. In the left sidebar, navigate to **OAuth2 -> URL Generator**:
   - **Scopes**:
     - `bot`
     - `applications.commands`
   - **Bot Permissions**:
     - `View Channels`
     - `Send Messages`
     - `Embed Links`
     - `Read Message History`
     - `Connect`
     - `Speak`
6. Copy the generated URL at the bottom, paste it into your browser, and select your Discord server to invite Void Vibe.

---

## 🔧 Lavalink v4 & Plugin Configuration

Lavalink v4 utilizes external plugins for advanced sources. The project is configured with:

1. **`dev.lavalink.youtube:youtube-plugin:1.18.2`**  
   Handles YouTube search and audio playback across multiple InnerTube clients (`ANDROID_VR`, `ANDROID_MUSIC`, `IOS`, `MWEB`, `WEB`, `MUSIC`, `WEBEMBEDDED`, `TV`). Fully compatible with Lavalink 4.2.2.
2. **`com.github.topi314.lavasrc:lavasrc-plugin:4.3.0`**  
   Provides Spotify and Apple Music metadata resolution.

### SoundCloud Format Failure Diagnosis & Fix
- **Root Cause**: Lavaplayer 2.2.6 (bundled in Lavalink 4.2.2) experienced format layout breaks with SoundCloud's web API, throwing `java.lang.RuntimeException: Did not detect any supported formats` and HTTP read timeouts when handling `scsearch:` queries. Because the bot previously used SoundCloud as its default search prefix, `/play <query>` consistently failed.
- **Fix Applied**: 
  1. Promoted YouTube (`ytsearch:`) to the primary default search provider in `services/music_service.py`.
  2. Upgraded YouTube plugin to `1.18.2` with expanded client fallbacks in `application.yml`.
  3. Added automatic fallback to YouTube Music (`ytmsearch:`) if primary YouTube resolution fails.
  4. Added user-friendly, source-specific error explanations when unsupported formats, missing credentials, or link restrictions occur.

### Diagnosing & Resolving Apple Music & Spotify Integration
- **Apple Music**: Disabled (`applemusic: false`) because it requires a valid Apple Developer MusicKit Media API token. If enabled without a token, LavaSrc crashes Lavalink on startup with `Apple Music API token is empty or null`.
- **Spotify**: Requires `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `.env` and `application.yml`. If unconfigured, Spotify web player token endpoints return HTTP 403. The bot detects Spotify URLs and guides users to play by song title directly: `/play <title>`.

---

## 🎵 Music Source Limitations & Link Handling

| Source | Status | How It Works |
| :--- | :--- | :--- |
| **YouTube** | 🟢 Default Search & Streams | Handled by `youtube-plugin` with OAuth support. Primary default search (`/play <title>`) and direct video/playlist links. |
| **YouTube Music** | 🟢 Automated Fallback | Handled by `youtube-plugin`. Automatic search fallback (`ytmsearch:`) if primary search fails. |
| **Bandcamp** | 🟢 Native Stream | Direct audio stream extraction without API keys. |
| **Twitch** | 🟢 Native Stream | Live audio streams supported directly. |
| **Direct URL** | 🟢 Native Stream | Direct MP3, AAC, FLAC, or OGG HTTP/HTTPS audio streams. |
| **Spotify** | 🟡 Requires API Keys | Set `SPOTIFY_CLIENT_ID` & `SPOTIFY_CLIENT_SECRET` in `.env` and `application.yml`. Otherwise search by song title: `/play <title>`. |
| **Apple Music** | ⚪ Disabled by Default | Requires an Apple Developer Media API token (`mediaAPIToken`). Disabled by default to prevent startup crashes. |
| **SoundCloud** | 🔴 Format Breaks in Lavaplayer | SoundCloud's API currently fails format detection (`Did not detect any supported formats`) in Lavaplayer 2.2.6. |

---

## 🧪 Testing and Verification

Void Vibe includes a comprehensive automated test suite testing queue mutations, pagination math, loop modes, volume ranges, permission checks, and music service provider classification/fallback routing.

To run the test suite:
```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected result:
```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\dell\Downloads\isbandu-portfolio
plugins: asyncio-1.4.0
collected 32 items

tests\test_music_service.py .......                                      [ 21%]
tests\test_queue.py ...........                                          [ 56%]
tests\test_validators.py ..............                                  [100%]

============================= 32 passed in 1.47s ==============================
```

---

## 🌐 24/7 Production VPS Deployment (Ubuntu 22.04 / 24.04 LTS)

When you are ready to host Void Vibe 24/7 so it remains online without your local computer running:

### Resource Recommendations
- **CPU**: 1–2 vCPUs
- **RAM**: 1.5–2 GB RAM (Lavalink Java heap: ~512MB, Python bot: ~150MB)
- **OS**: Ubuntu 22.04 or 24.04 LTS (Hetzner, DigitalOcean, Linode, or OVH)

### 1. Install Java 21 & Python
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y openjdk-21-jre-headless python3 python3-venv python3-pip git
```

### 2. Setup System User & Directory
```bash
sudo useradd -m -s /bin/bash voidvibe
sudo su - voidvibe
git clone <your-repository-url> ~/app
cd ~/app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Enter your real DISCORD_TOKEN
exit
```

### 3. Setup Systemd Service for Lavalink (`/etc/systemd/system/lavalink.service`)
```ini
[Unit]
Description=Void Vibe Lavalink Audio Node
After=network.target

[Service]
Type=simple
User=voidvibe
WorkingDirectory=/home/voidvibe/app
ExecStart=/usr/bin/java -Xmx512M -jar /home/voidvibe/app/Lavalink.jar
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

### 4. Setup Systemd Service for Void Vibe Bot (`/etc/systemd/system/voidvibe.service`)
```ini
[Unit]
Description=Void Vibe Discord Music Bot
After=network.target lavalink.service
Requires=lavalink.service

[Service]
Type=simple
User=voidvibe
WorkingDirectory=/home/voidvibe/app
ExecStart=/home/voidvibe/app/.venv/bin/python /home/voidvibe/app/bot.py
Restart=always
RestartSec=5
EnvironmentFile=/home/voidvibe/app/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 5. Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now lavalink.service
sudo systemctl enable --now voidvibe.service

# View live logs
sudo journalctl -u voidvibe.service -f
```

---

## 🔒 Security Guidance

- **Never Commit Secrets**: Ensure `.env` is listed in `.gitignore` and never committed to version control.
- **Token Protection**: If your Discord Bot Token or Lavalink Password is ever exposed, regenerate it immediately in the Discord Developer Portal.
- **Diagnostic Masking**: Void Vibe automatically masks tokens and passwords in console logs (`MTU2...EvdU`), preventing accidental credential leaks during screen shares or log sharing.
