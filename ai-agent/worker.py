import time
import json
from agent import call_premium_api
import asyncio

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
    print("\n🟢 Agent worker started...\n")

    while True:
        queue = load_queue()

        print(f"📨 Queue length: {len(queue)}")

        if queue:
            task = queue.pop(0)
            print(f"🚀 Running task: {task['type']}")

            try:
                if task["type"] == "call_premium_api":
                    print("🔧 Executing call_premium_api()...")
                    asyncio.run(call_premium_api())
                    print("✅ call_premium_api() done.")
            except Exception as e:
                print("❌ ERROR inside task:", e)

            save_queue(queue)

        time.sleep(2)

if __name__ == "__main__":
    worker()
