# mail2obsidian

A lightweight pipeline to send emails from Gmail to your Obsidian vault as Markdown notes.

## Features

- **Automated Polling**: Continuously checks an IMAP mailbox / label at a configurable interval.
- **HTML to Markdown**: Converts email bodies to clean Markdown with YAML frontmatter (sender, subject, date, Google Mail link).
- **Rclone Sync**: Automatically transfers new notes to your cloud-hosted Obsidian vault (e.g. Google Drive) using `rclone`.
- **Lightweight Docker Container**: Alpine-based image (~90 MB) managed easily with Docker Compose.

---

## Prerequisites

1. **Gmail Account**:
   - Create a filter for incoming emails (e.g., sent to `yourname+obsidian@gmail.com`).
   - Assign the label `Obsidian-Inbox` (or a label of your choice).
   - Generate a [Google App Password](https://myaccount.google.com/apppasswords).
2. **Rclone Configuration**:
   - Ensure you have an existing `rclone.conf` on your home server (usually at `~/.config/rclone/rclone.conf`) configured for your Obsidian remote (e.g., Google Drive).

---

## Quickstart (Docker Compose)

### 1. Clone & Configure

Clone the repository to your home server:

```bash
git clone https://github.com/yourusername/mail2obsidian.git
cd mail2obsidian
```

Create your configuration file from the template:

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials and paths:

```dotenv
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
GMAIL_LABEL=Privat/Obsidian
IMAP_SERVER=imap.gmail.com

# Polling interval in seconds (default: 600 = 10 minutes)
CHECK_INTERVAL=600

# Rclone remote target directory
RCLONE_REMOTE_PATH=gdrive:Dokumente/Obsidian/yourvault/00_Inbox

# Path to host rclone config directory (mounted into the container)
RCLONE_CONFIG_DIR=~/.config/rclone

# Timezone
TZ=Europe/Berlin
```

### 2. Start the Service

Start the container in the background:

```bash
docker compose up -d --build
```

### 3. Useful Commands

- **View Live Logs**:
  ```bash
  docker compose logs -f
  ```
- **Test a Single Run (without continuous polling)**:
  ```bash
  docker compose run --rm mail2obsidian python src/main.py --once
  ```
- **Restart the Service**:
  ```bash
  docker compose restart
  ```
- **Stop the Service**:
  ```bash
  docker compose down
  ```

---

## Local Development (Optional)

If you wish to run or test locally without Docker:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in .env
python src/main.py --once
```