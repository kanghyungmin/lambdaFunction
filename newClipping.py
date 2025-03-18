import imaplib
import email
import json
import requests
from email.header import decode_header
from datetime import datetime

# 환경 변수 (AWS Lambda에 저장)
IMAP_SERVER = "imap.gmail.com"  # Gmail IMAP 서버 (Outlook: imap.outlook.com)
EMAIL_ACCOUNT = ""
EMAIL_PASSWORD = ""  # 앱 비밀번호 사용
SLACK_WEBHOOK_URL = ""

def get_today_emails():
    """IMAP을 사용하여 오늘 날짜의 모든 이메일 가져오기"""
    try:
        # IMAP 서버 연결
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        print(f"Logged in as {EMAIL_ACCOUNT}")
        
        mail.select("inbox", True)

        # 오늘 날짜의 모든 이메일 가져오기
        today = datetime.today().strftime('%d-%b-%Y')
        result, data = mail.search(None, 'ON', today)
        email_ids = data[0].split()

        print(f"Search result: {result}")

        if not email_ids:
            return []

        emails = []
        for email_id in email_ids:
            result, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]

            msg = email.message_from_bytes(raw_email)
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes) and encoding:
                subject = subject.decode(encoding)

            sender = msg.get("From")
            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            emails.append({"subject": subject, "sender": sender, "body": body})

        mail.logout()

        return emails

    except Exception as e:
        print(f"Error: {e}")
        return []

def send_to_slack(emails):
    """Slack Webhook을 통해 여러 메시지 전송"""
    for email_data in emails:
        message = f"*📩 New Email Received*\n\n*From:* {email_data['sender']}\n*Subject:* {email_data['subject']}\n\n{email_data['body'][:-1]}..."  # 500자 제한
        payload = {"text": message}

        response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            print(f"Failed to send email to Slack: {response.status_code}")

def lambda_handler(event, context):
    """Lambda 핸들러 함수"""
    emails = get_today_emails()
    print(emails)
    if emails:
        send_to_slack(emails)
        return {"statusCode": 200, "body": "Emails sent to Slack"}
    return {"statusCode": 204, "body": "No new emails"}

emails = get_today_emails()
if emails:
    send_to_slack(emails)
    print("Emails sent to Slack")