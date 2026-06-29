<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src="https://telegra.ph/file/64d61b1f3933fbc18925e-4ba9274225dadacc17.jpg" width="90px" style="border-radius: 50%;" />
      </td>
      <td>
        <img src="https://readme-typing-svg.herokuapp.com?color=00BFFF&width=600&lines=Hey+There,+Welcome+to+Links+Share+Bot+⚡;Secure+Telegram+Invite+Link+Manager" />
      </td>
    </tr>
  </table>
</div>

<p align="center">
  <img src="https://komarev.com/ghpvc/?username=Xzrie&style=flat-square&color=0088cc&label=Profile+Views" />
</p>

<h1 align="center">
  <img src="https://readme-typing-svg.herokuapp.com?color=FF69B4&width=500&lines=Links+Share+Bot;Secure+Auto+Invite+Link+Generator" />
</h1>

<p align="center">
  <a href="https://t.me/LinkShare1_bot">
    <img src="https://img.shields.io/badge/Try%20Bot-%40LinkShare1__bot-blue?style=for-the-badge&logo=telegram&logoColor=white" />
  </a>
  &nbsp;
  <a href="https://t.me/MovieCrescent">
    <img src="https://img.shields.io/badge/Main%20Channel-%40MovieCrescent-0088cc?style=for-the-badge&logo=telegram&logoColor=white" />
  </a>
  &nbsp;
  <a href="https://t.me/xzrie">
    <img src="https://img.shields.io/badge/Owner-%40xzrie-blueviolet?style=for-the-badge&logo=telegram&logoColor=white" />
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Built%20With-Pyrogram-informational?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Database-MongoDB-success?style=flat-square&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-Telegram-2CA5E0?style=flat-square&logo=telegram&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" />
</p>

---

## 🌟 About

**Links Share Bot** ([@LinkShare1_bot](https://t.me/LinkShare1_bot)) is a powerful Telegram bot built for managing and distributing secure, auto-expiring invite links across private channels — all from a single unified admin panel.

Powered by **Pyrogram** and **MongoDB**, it handles multi-channel access control, force subscription enforcement, request-based link flows, and bulk generation at scale. Whether you're managing one channel or dozens, Amon keeps access clean, automated, and secure.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🔗 **Multi-Channel Support** | Manage invite links across multiple private channels simultaneously |
| 🔐 **Secure Expiring Links** | Auto-generated links that expire after use or time limit |
| 📦 **Bulk Link Generation** | Generate links for multiple channels in a single command |
| 📋 **Force Subscription** | Require users to join channels before accessing content |
| 📨 **Request Link System** | Users can request links; admins approve or deny them |
| 🛡️ **Admin Control Panel** | Granular admin permissions and multi-admin support |
| 📊 **User Statistics** | Track user interactions and bot usage metrics |
| 📡 **Channel Management Tools** | Add, remove, and list managed channels with ease |

---

## 🛠️ Commands

### 📡 Channel Management

| Command | Description |
|---|---|
| `/addch <channel_id>` | Add a channel to the bot's management list |
| `/delch <channel_id>` | Remove a channel from management |
| `/channels` | List all managed channels |
| `/links` | Display active invite links |
| `/bulklink <ids>` | Generate links for multiple channels at once |

### 📨 Request System

| Command | Description |
|---|---|
| `/reqlink` | Request an invite link |
| `/reqtime` | Set the cooldown time between requests |
| `/reqmode` | Toggle request mode on or off |
| `/approveon` | Enable auto-approval of link requests |
| `/approveoff` | Disable auto-approval of link requests |
| `/approveall` | Approve all pending link requests at once |

### 👑 Admin Commands

| Command | Description |
|---|---|
| `/addadmin` | Grant admin privileges to a user |
| `/broadcast` | Send a message to all bot users |
| `/stats` | View overall bot and user statistics |

---

## 🔑 Environment Variables

Create a `.env` file in the project root and populate the following:

```env
API_ID=               # Your Telegram API ID (from my.telegram.org)
API_HASH=             # Your Telegram API Hash
TG_BOT_TOKEN=         # Bot token from @BotFather
OWNER_ID=             # Telegram user ID of the bot owner
ADMINS=               # Comma-separated list of admin user IDs
DB_URL=               # MongoDB connection string
DB_NAME=              # MongoDB database name
DATABASE_CHANNEL=     # Channel ID used for internal data storage
```

---

## ⚙️ Deployment

### 🖥️ VPS / Local

```bash
git clone https://github.com/MatrixSparrow-coder/Links-Share-Bot.git
cd Links-Share-Bot
pip install -r requirements.txt
python3 main.py
```

### 🐳 Docker

```bash
docker build -t linksharebot .
docker run -d \
  --name linksharebot \
  --env-file .env \
  --restart always \
  linksharebot
```

---

## 💬 Support & Contact

Have a question or need help? Reach out through any of the channels below:

| Platform | Link |
|---|---|
| 🤖 Bot | [@LinkShare1_bot](https://t.me/LinkShare1_bot) |
| 📢 Channel | [@MovieCrescent](https://t.me/MovieCrescent) |
| 👤 Owner | [@xzrie](https://t.me/xzrie) |

---

## 📄 License

This project is released under the [MIT License](LICENSE). You are free to use, modify, and distribute this project with proper attribution.

---

## 🔖 Credits

Maintained by **Matrix**.

<p align="center">
  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif" />
</p>

<p align="center">
  <i>Built with ❤️ for the Telegram community</i>
</p>
