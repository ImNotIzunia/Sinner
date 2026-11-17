# Sinner

[![CI](https://github.com/ImNotIzunia/Sinner/actions/workflows/ci.yml/badge.svg)](https://github.com/ImNotIzunia/Sinner/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python)


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
```

The server owner is always whitelisted.

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
3. Still under the **Bot** tab, find the *Privileged Gateway Intents* section and enable **Message Content Intent**. This is only used to display the honeypot message content in alerts. If disabled, the bot will still work, but alerts will not include message content.

### 2. Invite the Bot on the server

Use the following link, replacing `YOUR_CLIENT_ID` with your *Application ID* (under the **General Information** tab):

```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=93188
```

The requested permissions are: Ban Members, View Channels, Send Messages, Manage Messages, Embed Links, and Read Message History.

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
| `ADMIN_CHANNEL_ID`       | ✅       | Admin channel ID (alerts)                                                          | —       |
| `WHITELIST_USER_IDS`     | ❌        | Comma-separated IDs of users allowed to post in the honeypot                       | Empty   |
| `WHITELIST_ROLE_IDS`     | ❌        | Comma-separated IDs of roles allowed to post in the honeypot                       | Empty   |
| `DELETE_HISTORY_SECONDS` | ❌        | Time window for deleting the banned user's message history (max `604800` = 7 days) | `3600`  |
| `AUTO_WARNING`           | ❌        | Automatically posts and pins a warning in the honeypot (`true` / `false`)          | `true`  |


## Troubleshooting

| Symptom                                                      | Possible Cause                                                                       |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| `Configure DISCORD_TOKEN, HONEYPOT_CHANNEL_ID...` on startup | Missing or incomplete `.env` file                                                    |
| `PrivilegedIntentsRequired`                                  | *Message Content Intent* is not enabled in the Developer Portal                      |
| "Ban failed" alert                                           | Bot role is below the target user's role, or the *Ban Members* permission is missing |
| Warning message not pinned                                   | Missing *Manage Messages* (or *Pin Messages*) permission in the channel              |
| Bot does not respond                                         | Incorrect channel ID, or the bot cannot access the channel                           |
| Alert does not include message content                       | *Message Content Intent* is disabled                                                 |


## Security

### CI

A GitHub Actions workflows `.github/workflows/ci.yml` runs on every push to `main` and on every pull request:
- **Linting** with *Ruff* (configuration in `ruff.toml`)
- **Compatibility checks** on Python 3.10, 3.11, 3.12, 3.13, and 3.14: dependency installation, compilation, and module imports

To run the same checks locally:

```bash
pip install ruff
ruff check .
python -c "import bot"
```

### Advises

- Never share any information written in the `.env` file.
- If your token is leaked, reset it immediately through the Developer Portal.


## Contribution

This is a personal project maintained by a single contributor.

All issues and pull requests are welcome. Please keep security and stability in mind when contributing.

You can also support the project by offering me a coffee !

<div align="center">

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/imnotizunia)