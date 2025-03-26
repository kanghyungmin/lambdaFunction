import json
import requests
import os

# 환경변수에서 Slack Webhook URL 가져오기
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
print(f"Slack Webhook URL: {SLACK_WEBHOOK_URL}")

def send_to_slack(message):
    """Slack으로 메시지를 전송하는 함수"""
    slack_message = {
        "text": f"*AWS SNS Notification(AutoScaling)*\n{message}"
    }

    response = requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(slack_message),
        headers={"Content-Type": "application/json"}
    )

    # Slack 메시지 전송 실패 시 오류 출력
    if response.status_code != 200:
        print(f"Failed to send message to Slack: {response.status_code}, Response: {response.text}")

def lambda_handler(event, context):
    """AWS SNS에서 메시지를 받아서 Slack으로 전송"""
    try:
        print("Received event:", json.dumps(event, indent=2))
        # pirnt()
        # SNS 메시지 추출
        for record in event.get("Records", []):
            sns_message = record.get("Sns", {}).get("Message", "No message content")
            sns_message_json = json.loads(sns_message)
            
            # JSON 데이터에서 안전하게 값 가져오기
            print("SNS Message JSON:", sns_message_json)
            event_type = sns_message_json.get("Event", "Unknown Event")

            cause = sns_message_json.get("Cause", "Unknown Cause")

            # 메시지 포맷 변경
            contents = f"*Event* : {event_type}\n*Cause* : {cause}"

            send_to_slack(contents)
        
        return {"statusCode": 200, "body": "Message sent to Slack"}
    
    except Exception as e:
        print(f"Error processing SNS event: {str(e)}")
        return {"statusCode": 500, "body": "Error processing SNS event"}
