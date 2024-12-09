from telethon import TelegramClient
import json
import asyncio

# Telegram API credentials
api_id = ''
api_hash = ''
phone_number = ''

# Telegram chat ID or username for Trojan bot
trojan_chat_id = '@solana_trojanbot'

# Path to the JSON file containing tokens
tokens_file = ""

# Function to load tokens from the JSON file
def load_tokens(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get("tokens", [])
    except Exception as e:
        print(f"Error reading tokens from {file_path}: {e}")
        return []

# Main function to send messages to Trojan
async def send_tokens_to_trojan():
    # Load tokens from the file
    tokens = load_tokens(tokens_file)

    if not tokens:
        print("No tokens found in the JSON file.")
        return

    # Prepare messages for each token
    messages = [f"{token['tokenAddress']}" for token in tokens]

    # Send messages to Trojan with a 1-second delay between each
    async with TelegramClient('ADD TROJAN SESSION FILE PATH', api_id, api_hash) as client:
        print("Logged in to Telegram successfully!")
        for message in messages:
            try:
                await client.send_message(trojan_chat_id, message)
                print(f"Sent: {message}")
                await asyncio.sleep(1)  # Wait 1 second before sending the next message
            except Exception as e:
                print(f"Error sending message '{message}': {e}")

# Entry point for the script
if __name__ == "__main__":
    asyncio.run(send_tokens_to_trojan())
