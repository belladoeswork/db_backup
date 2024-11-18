from typing import Optional
import requests
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import DatabaseLogger



class SlackNotifier:
    def __init__(self, webhook_url: Optional[str] = None, logger: Optional[DatabaseLogger] = None):
        self.logger = logger or DatabaseLogger()

        if webhook_url is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
            with open(config_path, 'r') as config_file:
                config = json.load(config_file)
                webhook_url = config.get('slack_webhook')
        
        if not webhook_url or not webhook_url.startswith('https://hooks.slack.com/services/'):
            self.logger.error("Invalid Slack webhook URL format")
            raise ValueError("Invalid Slack webhook URL format")
        
        self.webhook_url = webhook_url
        self.logger.info(f"Initialized SlackNotifier with webhook URL: {webhook_url[:35]}...")

    def send_notification(self, 
                        operation: str,
                        status: bool,
                        details: Optional[str] = None,
                        error: Optional[str] = None) -> bool:
        try:
            status_emoji = "✅" if status else "❌"
            status_text = "succeeded" if status else "failed"
            
            message = f"{status_emoji} Database {operation} {status_text}"
            if details:
                message += f"\n*Details:* {details}"
            if error:
                message += f"\n*Error:* {error}"
                
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message += f"\n_Timestamp: {timestamp}_"

            payload = {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }

            response = requests.post(self.webhook_url, json=payload)
            
            self.logger.info(f"Slack API response status code: {response.status_code}")
            self.logger.debug(f"Slack API response content: {response.text}")

            if response.status_code != 200:
                self.logger.error(f"Failed to send Slack notification. Status code: {response.status_code}")
                return False
            
            self.logger.info("Successfully sent Slack notification")    
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error sending Slack notification: {str(e)}")
            return False

        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {str(e)}")
            return False
               
    def test_connection(self) -> bool:
        try:
            self.logger.info("Testing Slack webhook connection")
            return self.send_notification(
                operation="connection test",
                status=True,
                details="This is a test notification to verify the webhook connection"
            )
        except Exception as e:
            self.logger.error(f"Slack connection test failed: {str(e)}")
            return False

if __name__ == "__main__":
    notifier = SlackNotifier()
    success = notifier.test_connection()
    if success:
        print("Slack webhook connection test succeeded.")
    else:
        print("Slack webhook connection test failed.")
