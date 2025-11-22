import time
import json
from agent import call_premium_api

QUEUE_FILE = "queue.json"

def load_queue():
    try:
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)

def worker():
    print("🟢 Agent worker running...")

    while True:
        queue = load_queue()

        if queue:
            task = queue.pop(0)
            print("📌 Running task:", task["type"])

            if task["type"] == "CALL_PREMIUM":
                call_premium_api()

            save_queue(queue)

        time.sleep(1)

if __name__ == "__main__":
    worker()
