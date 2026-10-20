import imaplib
import email
import re
from email.header import decode_header
from email.utils import parsedate_to_datetime, parseaddr
from urllib.parse import quote
import os
import logging
import subprocess
import signal
import sys
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
from markdownify import markdownify as md

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

stop_requested = False

def handle_signal(sig, frame):
    global stop_requested
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    stop_requested = True


def clean(text):
    # Replace only characters that are definitely illegal in filenames
    illegal = r'[<>:"/\\|?*]'
    cleaned = re.sub(illegal, "_", text)
    return cleaned.strip()

def get_body(msg):
    body = ""
    html_body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors='replace')
                    return body # Return plain text immediately if found
            
            elif content_type == "text/html" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    html_body = payload.decode(errors='replace')
        
        # If no plain text was found but HTML was, convert it
        if html_body:
            return md(html_body)
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            if content_type == "text/html":
                return md(payload.decode(errors='replace'))
            else:
                return payload.decode(errors='replace')
    
    return body

def process_emails():
    load_dotenv()
    
    username = os.getenv("GMAIL_EMAIL")
    password = os.getenv("GMAIL_APP_PASSWORD")
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
    label = os.getenv("GMAIL_LABEL", "Obsidian-Inbox")
    output_dir = os.getenv("OUTPUT_DIR", "./inbox")

    if not username or not password:
        logger.error("GMAIL_EMAIL or GMAIL_APP_PASSWORD not set in .env")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        # create an IMAP4 class with SSL 
        imap = imaplib.IMAP4_SSL(imap_server)
        # authenticate
        imap.login(username, password)
        
        status, messages = imap.select(label)
        if status != "OK":
            logger.error(f"Could not select label {label}")
            return

        # search for all unseen emails
        status, response = imap.search(None, "UNSEEN")
        if status != "OK":
            logger.error("Error searching for emails")
            return

        email_ids = response[0].split()
        logger.info(f"Found {len(email_ids)} new emails")

        for e_id in email_ids:
            # fetch the email message by ID
            res, msg_data = imap.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # parse a bytes email into a message object
                    msg = email.message_from_bytes(response_part[1])
                    # decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        # if it's bytes, decode to str
                        subject = subject.decode(encoding or "utf-8")
                    
                    # decode email sender
                    from_, encoding = decode_header(msg.get("From"))[0]
                    if isinstance(from_, bytes):
                        from_ = from_.decode(encoding or "utf-8")
                    
                    logger.info(f"Processing email: {subject} from {from_}")
                    
                    body = get_body(msg)

                    # Extract metadata for YAML
                    from_header = msg.get("From")
                    _, from_email = parseaddr(from_header)
                    
                    date_header = msg.get("Date")
                    try:
                        dt = parsedate_to_datetime(date_header)
                        formatted_date = dt.strftime("%d.%m.%Y, %H:%M")
                    except Exception:
                        formatted_date = date_header

                    msg_id = msg.get("Message-ID")
                    source_url = f"https://mail.google.com/mail/u/0/#search/rfc822msgid%3A{quote(msg_id)}" if msg_id else "Gmail"
                    
                    # Escape double quotes in subject for YAML
                    yaml_title = subject.replace('"', '\\"')
                    
                    yaml_frontmatter = f"""---
title: "{yaml_title}"
source: "Gmail"
source_url: "{source_url}"
from_email: "{from_email}"
date: "{formatted_date}"
---

"""
                    full_content = yaml_frontmatter + body
                    
                    # Create filename from subject
                    filename = clean(subject) + ".md"
                    filepath = os.path.join(output_dir, filename)
                    
                    # If file exists, append a timestamp to avoid overwrite? 
                    # Or just overwrite? Obsidian usually handles duplicates or we can use unique names.
                    if os.path.exists(filepath):
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        filename = f"{clean(subject)}_{timestamp}.md"
                        filepath = os.path.join(output_dir, filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(full_content)
                    
                    logger.info(f"Saved to {filepath}")
                    
                    # Mark as read (implicitly done by fetch in some servers, but let's be explicit)
                    imap.store(e_id, '+FLAGS', r'\Seen')

        # close the connection and logout
        imap.close()
        imap.logout()

        # Rclone sync if configured
        rclone_remote = os.getenv("RCLONE_REMOTE_PATH")
        if rclone_remote and os.listdir(output_dir):
            logger.info(f"Syncing {output_dir} to {rclone_remote} via rclone")
            try:
                # rclone move might be better if we want to clear the local inbox
                # but rclone copy is safer. Let's use move to keep local clean after sync.
                subprocess.run(["rclone", "move", output_dir, rclone_remote], check=True)
                logger.info("Rclone sync completed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Rclone failed with error: {e}")
            except FileNotFoundError:
                logger.error("rclone command not found. Please install it.")

    except Exception as e:
        logger.exception(f"An error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description="Mail to Obsidian Parser")
    parser.add_argument("--once", action="store_true", help="Run once and exit instead of continuous loop")
    parser.add_argument("--interval", type=int, default=None, help="Polling interval in seconds (overrides CHECK_INTERVAL)")
    args = parser.parse_args()

    load_dotenv()

    run_once = args.once or os.getenv("RUN_ONCE", "false").lower() in ("true", "1", "yes")
    
    interval = args.interval
    if interval is None:
        try:
            interval = int(os.getenv("CHECK_INTERVAL", "600"))
        except ValueError:
            interval = 600

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    if run_once:
        logger.info("Executing mail2obsidian in one-shot mode...")
        process_emails()
        return

    logger.info(f"Starting mail2obsidian daemon (polling every {interval}s)...")
    while not stop_requested:
        process_emails()
        
        # Sleep in 1-second intervals to promptly respond to termination signals
        for _ in range(interval):
            if stop_requested:
                break
            time.sleep(1)

    logger.info("mail2obsidian daemon stopped gracefully.")

if __name__ == "__main__":
    main()

