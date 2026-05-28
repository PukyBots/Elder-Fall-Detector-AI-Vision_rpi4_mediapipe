import requests

NTFY_TOPIC = "id_1"

def send_alert(message):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode()
        )
    except Exception as e:
        print("ntfy error:", e)