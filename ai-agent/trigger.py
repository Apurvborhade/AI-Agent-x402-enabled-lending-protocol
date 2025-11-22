import json

QUEUE_FILE = "queue.json"

def send_task(task):
    try:
        with open(QUEUE_FILE, 'r') as file:
            queue = json.load(file)
    except FileNotFoundError:
        queue = []
    
    queue.append(task)
    
    with open(QUEUE_FILE, 'w') as file:
        json.dump(queue, file,indent=2)
        
send_task({"type": "call_premium_api"})
print("📬 Task sent to agent!")  