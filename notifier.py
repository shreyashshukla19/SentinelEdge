import os
import json
import requests
from datetime import datetime


class SafetyNotifier:
    def __init__(self, webhook_url=None, platform="discord"):
        """
        Initializes the notifier with a Discord or Telegram webhook URL.
        """
        self.webhook_url = webhook_url or os.getenv("SAFETY_WEBHOOK_URL")
        self.platform = platform.lower()

    def send_alert(self, violation_type, zone, confidence, image_path=None):
        """
        Sends an alert message to the configured webhook (Discord or Telegram).
        """
        if self.platform not in {"discord", "telegram"}:
            return {"status": "error", "reason": "Unsupported platform"}

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.platform == "discord":
            message = (
                f"🚨 **SAFETY VIOLATION DETECTED** 🚨\n"
                f"• **Violation:** {violation_type}\n"
                f"• **Zone:** {zone}\n"
                f"• **Confidence:** {confidence:.2f}\n"
                f"• **Time:** {timestamp}"
            )
        else:
            message = (
                f"🚨 SAFETY VIOLATION DETECTED 🚨\n"
                f"Violation: {violation_type}\n"
                f"Zone: {zone}\n"
                f"Confidence: {confidence:.2f}\n"
                f"Time: {timestamp}"
            )

        if not self.webhook_url:
            print(f"[SIMULATION NOTIFICATION] {message}")
            return {"status": "simulated", "message": message}

        try:
            if self.platform == "discord":
                if image_path:
                    with open(image_path, "rb") as image_file:
                        response = requests.post(
                            self.webhook_url,
                            data={"payload_json": json.dumps({"content": message})},
                            files={"file": (os.path.basename(image_path), image_file)},
                            timeout=10,
                        )
                else:
                    response = requests.post(
                        self.webhook_url,
                        json={"content": message},
                        timeout=10,
                    )
            elif self.platform == "telegram":
                chat_id = os.getenv("TELEGRAM_CHAT_ID")
                if not chat_id:
                    return {"status": "error", "reason": "TELEGRAM_CHAT_ID is not configured"}

                if image_path:
                    photo_url = self.webhook_url
                    if photo_url.endswith("/sendMessage"):
                        photo_url = f"{photo_url[:-len('sendMessage')]}sendPhoto"
                    with open(image_path, "rb") as image_file:
                        response = requests.post(
                            photo_url,
                            data={"chat_id": chat_id, "caption": message},
                            files={"photo": image_file},
                            timeout=10,
                        )
                else:
                    response = requests.post(
                        self.webhook_url,
                        json={"chat_id": chat_id, "text": message},
                        timeout=10,
                    )

            if response.status_code in [200, 204]:
                return {"status": "success", "response_code": response.status_code}
            else:
                return {"status": "failed", "response_code": response.status_code, "text": response.text}
                
        except (OSError, requests.RequestException) as e:
            print(f"Failed to send webhook notification: {e}")
            return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    # Test notification locally
    notifier = SafetyNotifier()
    notifier.send_alert("Missing Hard Hat", "Sector B - Assembly Line", 0.92)