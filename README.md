# mail2obsidian

A simple pipeline to send emails to your Obsidian vault.

## Prerequisites

1.  **Gmail Account**:
    *   Create a filter for emails sent to `yourname+obsidian@gmail.com`.
    *   Label them `Obsidian-Inbox`.
    *   Generate a [Google App Password](https://myaccount.google.com/apppasswords).
2.  **Rclone**:
    *   Install Rclone on your server.
    *   Configure it to access your Google Drive (where your Obsidian vault is).
    *   Mount the vault or use `rclone copy` in a post-process script.

## Setup

1.  Clone this repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Copy `.env.example` to `.env` and fill in your details:
    ```bash
    cp .env.example .env
    ```
4.  Run the script:
    ```bash
    python src/main.py
    ```

## Automation

You can set up a cron job to run this every 5 minutes:

```cron
*/5 * * * * cd /path/to/mail2obsidian && /usr/bin/python3 src/main.py >> /var/log/mail2obsidian.log 2>&1
```

### Systemd (Alternative)

1.  Copy the service and timer files to `~/.config/systemd/user/`:
    ```bash
    mkdir -p ~/.config/systemd/user/
    cp mail2obsidian.service mail2obsidian.timer ~/.config/systemd/user/
    ```
2.  Edit `mail2obsidian.service` to set the correct `WorkingDirectory` and `ExecStart` paths.
3.  Reload systemd and enable the timer:
    ```bash
    systemctl --user daemon-reload
    systemctl --user enable --now mail2obsidian.timer
    ```
