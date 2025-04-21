import json
import os

# Define the path for the persistent storage file
WEBHOOK_STORAGE_FILE = "/app/webhooks.json"

def load_webhooks():
    """Load webhooks from the persistent storage file."""
    if not os.path.exists(WEBHOOK_STORAGE_FILE):
        # Create the file with an empty list if it doesn't exist
        with open(WEBHOOK_STORAGE_FILE, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(WEBHOOK_STORAGE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading webhooks: {e}")
        return []

def save_webhook(webhook):
    """Save a new webhook to the persistent storage file."""
    webhooks = load_webhooks()
    webhooks.append(webhook)
    try:
        with open(WEBHOOK_STORAGE_FILE, "w") as f:
            json.dump(webhooks, f, indent=4)
    except IOError as e:
        print(f"Error saving webhook: {e}")

def clear_webhooks():
    """Clear all webhooks from the persistent storage file."""
    try:
        with open(WEBHOOK_STORAGE_FILE, "w") as f:
            json.dump([], f)
    except IOError as e:
        print(f"Error clearing webhooks: {e}")

def download_webhook():
    """Download the webhook storage file."""
    if os.path.exists(WEBHOOK_STORAGE_FILE):
        return WEBHOOK_STORAGE_FILE
    else:
        print(f"Webhook storage file does not exist: {WEBHOOK_STORAGE_FILE}")
        return None
    

    