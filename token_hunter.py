import requests
from datetime import datetime
import json
import subprocess

# Consolidated function for fetching detailed token data
def fetch_detailed_data(addresses):
    detailed_data = []
    for i in range(0, len(addresses), 30):
        chunk = addresses[i:i+30]
        token_addresses_str = ','.join(chunk)
        detailed_data_url = f'https://api.dexscreener.com/latest/dex/tokens/{token_addresses_str}'
        response = requests.get(detailed_data_url)
        if response.status_code == 200:
            detailed_data.extend(response.json().get('pairs', []))
        else:
            print(f"Failed to fetch data for chunk: {chunk}")
    return detailed_data

# Fetch Latest Boosted Tokens
def get_latest_boosted_tokens():
    url = 'https://api.dexscreener.com/token-boosts/latest/v1'
    response = requests.get(url)
    if response.status_code == 200:
        # Ensure response is a list and extract token addresses
        boosted_tokens = response.json()
        if isinstance(boosted_tokens, list):
            return boosted_tokens
    print("Failed to fetch latest boosted tokens or unexpected response format.")
    return []


# Fetch Most Boosted Tokens
def get_most_boosted_tokens():
    url = 'https://api.dexscreener.com/token-boosts/top/v1'
    response = requests.get(url)
    if response.status_code == 200:
        boosted_tokens = response.json()
        if isinstance(boosted_tokens, list):
            return boosted_tokens
    print("Failed to fetch most boosted tokens or unexpected response format.")
    return []

# Fetch New Tokens
def get_new_tokens():
    url = 'https://api.dexscreener.com/token-profiles/latest/v1'
    response = requests.get(url)
    if response.status_code == 200:
        new_tokens = response.json()
        if isinstance(new_tokens, list):
            return new_tokens
    print("Failed to fetch new tokens or unexpected response format.")
    return []


# Filters with permanent thresholds for core stability
def filter_tokens(detailed_data):
    selected_tokens = []
    MIN_LIQUIDITY_USD = 50000  # Minimum liquidity
    MAX_LIQUIDITY_USD = 500000  # Maximum liquidity
    MIN_TXNS_LAST_HOUR = 100  # Minimum transactions per hour
    MAX_TXNS_LAST_HOUR = 1000  # Maximum transactions per hour
    MAX_PRICE_CHANGE_H1 = 30  # Maximum hourly price change (%)
    MIN_PRICE_CHANGE_H1 = 0  # Minimum hourly price change (%)

    for pair in detailed_data:
        base_token = pair.get("baseToken", {})
        liquidity = pair.get("liquidity", {})
        txns = pair.get("txns", {})
        price_change = pair.get("priceChange", {})
        token_address = base_token.get("address")

        liquidity_usd = liquidity.get("usd", 0)
        txns_h1 = txns.get("h1", {}).get("buys", 0) + txns.get("h1", {}).get("sells", 0)
        price_change_h1 = price_change.get("h1", 0)

        if (
            MIN_LIQUIDITY_USD <= liquidity_usd <= MAX_LIQUIDITY_USD
            and MIN_TXNS_LAST_HOUR <= txns_h1 <= MAX_TXNS_LAST_HOUR
            and MIN_PRICE_CHANGE_H1 <= price_change_h1 <= MAX_PRICE_CHANGE_H1
        ):
            selected_tokens.append({
                "tokenAddress": token_address,
                "name": base_token.get("name"),
                "symbol": base_token.get("symbol"),
                "liquidityUsd": liquidity_usd,
                "transactionsLastHour": txns_h1,
                "priceChangeH1": price_change_h1
            })
    print(f"{len(selected_tokens)} tokens passed the filters.")
    return selected_tokens

# Updated scoring function to prioritize consistent performance
def calculate_score(token):
    transactions = token.get("transactionsLastHour", 0)
    liquidity = token.get("liquidityUsd", 0)
    price_change = token.get("priceChangeH1", 0)

    # Adjusted weights for stable token prioritization
    return (transactions * 1.5) + (liquidity * 0.1) + (price_change * 2)

# Main Execution
def main():
    latest_boosted_tokens = get_latest_boosted_tokens()
    most_boosted_tokens = get_most_boosted_tokens()
    new_tokens = get_new_tokens()

    all_token_addresses = set(
        token.get('tokenAddress') for token in (latest_boosted_tokens + most_boosted_tokens + new_tokens)
    )

    detailed_data = fetch_detailed_data(list(all_token_addresses))
    filtered_tokens = filter_tokens(detailed_data)
    top_tokens = sorted(filtered_tokens, key=calculate_score, reverse=True)[:10]

    output = {
        "timestamp": datetime.now().isoformat(),
        "tokens": top_tokens
    }

    output_file = "/Users/josephdire/Dev/memeshot/tokens.json"
    with open(output_file, "w") as file:
        json.dump(output, file, indent=4)

    print(f"Final filtered tokens written to {output_file}")

    #subprocess.run(["python3", "/Users/josephdire/Dev/memeshot/token_sender.py", output_file])

if __name__ == "__main__":
    main()
