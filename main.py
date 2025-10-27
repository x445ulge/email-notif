from email.parser import BytesParser
from email.policy import default
import json
import poplib
import subprocess
import time


with open(".config.json") as f:
    CONFIG = json.load(f)

# POP3 server details
POP3_CONFIG = CONFIG["pop3"]

POP3_SERVER = POP3_CONFIG["server"]
POP3_PORT = POP3_CONFIG["port"]  # Usually 110 or 995 for SSL
USERNAME = POP3_CONFIG["email_username"]
PASSWORD = POP3_CONFIG["email_password"]

# Notification settings
NOTIF_CONFIG = CONFIG["notifications"]

EMAIL_COUNT = NOTIF_CONFIG["email_count"]
CHECK_INTERVAL = NOTIF_CONFIG["check_interval"]  # in seconds


def get_mail_count():
    try:
        server = poplib.POP3(POP3_SERVER, POP3_PORT, timeout=10)
        server.user(USERNAME)
        server.pass_(PASSWORD)

        message_count, _ = server.stat()
        server.quit()
        return message_count
    except Exception as e:
        print(f"Error connecting to POP3 server: {e}")
        return None


def fetch_subjects(start_index):
    subjects = []
    try:
        server = poplib.POP3(POP3_SERVER, POP3_PORT, timeout=10)
        server.user(USERNAME)
        server.pass_(PASSWORD)

        # For each new message, fetch headers and parse subject
        for i in range(start_index, start_index + EMAIL_COUNT):
            try:
                response, lines, octets = server.top(i, 0)  # Fetch headers only
                msg_data = b"\n".join(lines)
                msg = BytesParser(policy=default).parsebytes(msg_data)
                subject = msg["subject"]
                if subject is None:
                    subject = "(No Subject)"
                subjects.append(subject)
            except Exception as e:
                print(f"Error fetching message {i}: {e}")

        server.quit()
    except Exception as e:
        print(f"Error connecting to POP3 server while fetching subjects: {e}")

    return subjects


def notify_new_mail(new_count, subjects):
    if new_count == 1:
        message = f"1 new email: 📬 {subjects[0]}"
    else:
        subject_list = "\n".join(f"📬 {subj}" for subj in subjects)
        message = f"{new_count} new emails:\n{subject_list}"

    # uses snoretoast [https://github.com/KDE/snoretoast] for reliable notifications
    _ = subprocess.run(
        [
            "snoretoast.exe",
            "-t",
            "Mail Alert!",
            "-m",
            message,
            "-p",
            "assets/mailbox.png",
        ]
    )


def main():
    last_count = 0
    while True:
        mail_count = get_mail_count()
        if mail_count is None:
            print("Could not fetch mail count. Retrying...")
        else:
            if mail_count > last_count:
                new_emails = mail_count - last_count
                subjects = fetch_subjects(last_count + 1)  # POP3 messages start at 1
                notify_new_mail(new_emails, subjects)
            last_count = mail_count

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
    