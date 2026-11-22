<p align="center">
  <img src="assets/banner.png" alt="DISCORD-MUSIC-BOT Banner" width="100%">
</p>

# ◈ Void Vibe — Discord Music Bot

[![CI](https://github.com/ISBANDURAHUMAN-R/DISCORD-MUSIC-BOT/actions/workflows/ci.yml/badge.svg)](https://github.com/ISBANDURAHUMAN-R/DISCORD-MUSIC-BOT/actions)

## ◆ About the Project
Void Vibe is an audio streaming Discord bot built with Python, discord.py, and Lavalink v4. It provides independent per-server audio playback queues, interactive Discord button controls, and multi-source audio resolution across Discord voice channels. The bot features automated voice state cleanup, disconnect timers, and credential masking.

```mermaid
flowchart TD
    User["&nbsp; Discord Guild &nbsp;<br/>&nbsp; Members &nbsp;"] --> Slash["&nbsp; Discord Slash &nbsp;<br/>&nbsp; Commands &nbsp;<br/>&nbsp; (/play, /queue) &nbsp;"]
    Slash --> Gateway["&nbsp; Discord Gateway &nbsp;<br/>&nbsp; &amp; discord.py &nbsp;"]
    Gateway --> Cogs["&nbsp; Music Cogs &amp; &nbsp;<br/>&nbsp; State Validators &nbsp;"]
    Cogs --> Wavelink["&nbsp; Wavelink 3.5 &nbsp;<br/>&nbsp; Client &nbsp;"]
    Wavelink -->|"&nbsp; WebSocket IPC &amp; &nbsp;<br/>&nbsp; Audio Stream &nbsp;"| Lavalink["&nbsp; Lavalink v4 &nbsp;<br/>&nbsp; Java Node &nbsp;"]
    Lavalink -->|"&nbsp; PCM Packets &nbsp;"| VoiceChannel["&nbsp; Discord Voice &nbsp;<br/>&nbsp; Channel (UDP) &nbsp;"]
```

## ❖ Key Features
- Lavalink v4 architecture powered by Wavelink 3.5 with WebSocket audio encoding.
- 14 native Discord application slash commands with parameter auto-completion and validation.
- Interactive Discord UI button controls attached directly to player embeds.
- Isolated per-guild queuing supporting single-track and whole-queue loop modes.
- Automated voice channel departure on inactivity or listener abandonment.
- Automated unit test suite covering queue pagination, loop math, and provider fallback logic.

## ⬢ Technologies Used
- Python 3.12+
- discord.py 2.x
- Wavelink 3.5
- Lavalink v4
- Java 21 LTS
- pytest

## § Requirements
- Python 3.12 or higher
- Java Runtime Environment (JRE) 17 or 21
- Lavalink v4.x binary (`Lavalink.jar`)
- Discord Bot Token

## ▲ Installation & Execution
```bash
# 1. Install dependencies
python -m pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Edit .env with your DISCORD_TOKEN and LAVALINK_PASSWORD

# 3. Start Lavalink server
java -jar Lavalink.jar

# 4. Start the bot
python bot.py
```

## ※ Developer
Developer: ISBANDU RAHUMAN R  
GitHub: https://github.com/ISBANDURAHUMAN-R
