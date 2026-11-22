# Sinner

[![CI](https://github.com/ImNotIzunia/Sinner/actions/workflows/ci.yml/badge.svg)](https://github.com/ImNotIzunia/Sinner/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python)


Sinner is a Discord *anti-bot* Bot based on the **honeypot** principle. 



---

## Table of contents

1. [How it works](#how-it-works)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Security](#security)
7. [Contribution](#contribution)


## How it works

```
Message posted in the honeypot channel
        │
        ├── Is the author whitelisted? ──► Yes: message is kept (moderation alert)
        │
        ▼ No
 1. Delete the message
 2. Ban the user (+ purge recent message history)
 3. Send an alert to the admin channel ──► "Unban" button available for false positives


 New member joins the server
 1. Compute a risk score (account age, avatar, username, time to join, raid...)
 2. Detect which invite was used
 3. Post a profile in the admin channel ──► "Ban" / "Kick" buttons available
```

The server owner is always whitelisted in the honeypot channel. All the buttons keep working even if the bot is restarted.

### Member profiling

Each new member gets a profile in the admin channel, with a **risk score from 0 to 100**, the list of suspicious and reassuring signals, and the invite used to join the server. The score is **only indicative**: it helps moderators to decide, and *Sinner* will never ban automatically a user based on the score.

| Signal                                                           | Points          |
| ---------------------------------------------------------------- | --------------- |
| Account created less than 24 h / 7 days / 30 days ago           | +40 / +25 / +10 |
| Joined less than 10 min after the account was created            | +15             |
| Default avatar                                                   | +10             |
| No Discord badge                                                 | +5              |
| Username with a link or spam keyword (`discord.gg`, `nitro`...)  | +30             |
| Username ending with 4 or more digits                            | +10             |
| Raid in progress                                                 | +20             |
 
Levels: 🟢 below 20 · 🟡 20 to 44 · 🟠 45 to 69 · 🔴 70 and above.

A **Raid Alert** is also posted when `RAID_JOINS` members join within `RAID_WINDOW` seconds. (See `.env.example` for configuration.)

### Best Practices

- Make sure that the channel can be visible to all members when arriving on the server.
- Place the channel at the top or bottom of the list and give it a clear name (e.g. *do-no-post*).
- The pinned warning message helps prevent false positives: keep `AUTO_WARNING=true`


## Requirements

- Python 3.10 or newer (tested with 3.14)
- A Discord bot created through the [Developer Portal](https://discord.com/developers/applications)


## Installation

### 1. Create a Discord Bot

1. Go to the [Developer Portal](https://discord.com/developers/applications) → **New Application**.
2. Open the **Bot** tab → **Reset Token** and copy your token (never share it).
3. Still under the **Bot** tab, find the *Privileged Gateway Intents* section and enable:
   - **Message Content Intent**: only used to display the honeypot message content in alerts. If disabled, the bot will still work, but alerts will not include message content.
   - **Server Members Intent**: required to profile new members. If you don't want to enable it, set `PROFILING=false` in your `.env`.

### 2. Invite the Bot on the server

Use the following link, replacing `YOUR_CLIENT_ID` with your *Application ID* (under the **General Information** tab):

```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=93222
```

> ⚠️ The **`bot`** scope is mandatory. Without it, the server shows "This application has no bot in this server".

The requested permissions are: Ban Members, Kick Memebers, View Channels, Send Messages, Manage Messages, Embed Links, Read Message History and **Manage Server** (only used to detect which invited a new member used - without it, the profile shows "Unknown").

> ⚠️ Under *Server Settings → Roles*, place the bot's role **above** the roles it needs to be able to ban. Discord does not allow a bot to ban members whose roles are equal to or higher than its own.

### 3. Install and Configure

```Bash
git clone https://github.com/ImNotIzunia/Sinner.git
cd Sinner

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit .env
```

To retrieve an ID: go to *Discord Settings → Advanced → Developer Mode*, then right-click a channel, user, or role → **Copy ID**.

### 4. Launch the Bot

```Bash
python main.py
```


## Configuration

For the `.env` file. You can see the `.env.example` as a reference.

| Variable                 | Required | Description                                                                        | Default |
| ------------------------ | -------- | ---------------------------------------------------------------------------------- | ------- |
| `DISCORD_TOKEN`          | ✅       | Bot token                                                                          | —       |
| `HONEYPOT_CHANNEL_ID`    | ✅       | Honeypot channel ID                                                                | —       |
| `ADMIN_CHANNEL_ID`       | ✅       | Admin channel ID (alerts, member profiles, update notices)                         | —       |
| `WHITELIST_USER_IDS`     | ❌        | Comma-separated IDs of users allowed to post in the honeypot                       | Empty   |
| `WHITELIST_ROLE_IDS`     | ❌        | Comma-separated IDs of roles allowed to post in the honeypot                       | Empty   |
| `DELETE_HISTORY_SECONDS` | ❌        | Time window for deleting the banned user's message history (max `604800` = 7 days) | `3600`  |
| `AUTO_WARNING`           | ❌        | Automatically posts and pins a warning in the honeypot (`true` / `false`)          | `true`  |
| `PROFILING`              | ❌        | Profile new members in the admin channel (needs the *Server Members Intent*)       | `true`  |
| `RAID_JOINS`             | ❌        | Number of joins that triggers a raid alert...                                      | `5`     |
| `RAID_WINDOW`            | ❌        | ...within this time window, in seconds                                             | `60`    |
| `UPDATE_CHECK`           | ❌        | Check GitHub for new versions                                                      | `true`  |
| `UPDATE_CHECK_HOURS`     | ❌        | How often to check, in hours                                                       | `6`     |
 

## Updates

The bot **never updates itself** : it only notifies the admin channel when a new version is available.

Every `UPDATE_CHECK_HOURS` hours, the bot asks the public GitHub API for the latest release. (`/releases/latest`, anonymous - no data sent). If a newer version than yours exists, it posts a message in the admin channel with the release notes, once per version.

To update the bot, simply run the following commands in the bot's directory:

```bash
git pull
pip install -r requirements.txt
python main.py
```

Set the `UPDATE_CHECK=false` in the `.env` file to disable the update check. Only **releases** trigger a notifications, not plain commits.


## Troubleshooting

| Symptom                                                      | Possible Cause                                                                       |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| `Configure DISCORD_TOKEN, HONEYPOT_CHANNEL_ID...` on startup | Missing or incomplete `.env` file                                                    |
| `PrivilegedIntentsRequired`                                  | *Message Content Intent* or *Server Members Intent* is not enabled (or set `PROFILING=false`) |
| "This application has no bot in this server"                 | The bot was invited without the `bot` scope: use the invite link above               |
| "Ban failed" alert                                           | Bot role is below the target user's role, or the *Ban Members* permission is missing |
| Warning message not pinned                                   | Missing *Manage Messages* (or *Pin Messages*) permission in the channel              |
| Bot does not respond                                         | Incorrect channel ID, or the bot cannot access the channel                           |
| Alert does not include message content                       | *Message Content Intent* is disabled                                                 |
| Invite always shown as "Unknown"                             | Missing *Manage Server* permission, or the invite was a vanity / single-use link     |
| No update notification                                       | No release published yet, or `UPDATE_CHECK=false`                                    |
| `GitHub rate limit reached` in the console                   | Anonymous GitHub quota (60/h per IP): the bot retries on the next cycle              |


## Security

### CI

Two GitHub Actions workflows live in `.github/workflows/`:
 
- **`ci.yml`** runs on every push to `main` and on every pull request:
  - **Linting** with *Ruff* (configuration in `ruff.toml`)
  - **Compatibility checks** on Python 3.10, 3.11, 3.12, 3.13, and 3.14: dependency installation, compilation, module imports, and `pytest`
- **`release.yml`** runs on every `vX.Y.Z` tag and creates the GitHub release (see [Updates](#updates)).

To run the same checks locally:

```bash
pip install ruff pytest
ruff check .
pytest
```

### Advises

- Never share any information written in the `.env` file.
- If your token is leaked, reset it immediately through the Developer Portal.
- Release notes displayed by the bot cannot mention `@everyone` or roles.
- The update check is a single anonymous `GET` request to `api.github.com`.


## Contribution

This is a personal project maintained by a single contributor.

All issues and pull requests are welcome. Please keep security and stability in mind when contributing.

You can also support the project by offering me a coffee !

<div align="center">

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/imnotizunia)