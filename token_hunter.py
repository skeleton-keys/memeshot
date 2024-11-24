import requests
from datetime import datetime
import json

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
    return response.json() if response.status_code == 200 else []

# Fetch Most Boosted Tokens
def get_most_boosted_tokens():
    url = 'https://api.dexscreener.com/token-boosts/top/v1'
    response = requests.get(url)
    return response.json() if response.status_code == 200 else []

# Fetch New Tokens
def get_new_tokens():
    url = 'https://api.dexscreener.com/token-profiles/latest/v1'
    response = requests.get(url)
    return response.json() if response.status_code == 200 else []

# Remove duplicates by token address
def remove_duplicates(tokens):
    seen_addresses = set()
    unique_tokens = []
    for token in tokens:
        token_address = token.get("tokenAddress")
        if token_address and token_address not in seen_addresses:
            unique_tokens.append(token)
            seen_addresses.add(token_address)
    return unique_tokens

# Filters for latest boosted tokens
def filter_latest_boosted_tokens(detailed_data):
    selected_tokens = []
    MIN_LIQUIDITY_USD = 5000
    MIN_TXNS_LAST_HOUR = 20
    MAX_PRICE_CHANGE_H1 = 50
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
            liquidity_usd >= MIN_LIQUIDITY_USD
            and txns_h1 >= MIN_TXNS_LAST_HOUR
            and price_change_h1 <= MAX_PRICE_CHANGE_H1
        ):
            selected_tokens.append({
                "tokenAddress": token_address,
                "name": base_token.get("name"),
                "symbol": base_token.get("symbol"),
                "liquidityUsd": liquidity_usd,
                "transactionsLastHour": txns_h1,
                "priceChangeH1": price_change_h1
            })
    return selected_tokens

# Filters for most boosted tokens
def filter_most_boosted_tokens(detailed_data):
    selected_tokens = []
    MIN_LIQUIDITY_USD = 10000
    MIN_TXNS_LAST_HOUR = 50
    for pair in detailed_data:
        base_token = pair.get("baseToken", {})
        liquidity = pair.get("liquidity", {})
        txns = pair.get("txns", {})
        token_address = base_token.get("address")

        liquidity_usd = liquidity.get("usd", 0)
        txns_h1 = txns.get("h1", {}).get("buys", 0) + txns.get("h1", {}).get("sells", 0)

        if liquidity_usd >= MIN_LIQUIDITY_USD and txns_h1 >= MIN_TXNS_LAST_HOUR:
            selected_tokens.append({
                "tokenAddress": token_address,
                "name": base_token.get("name"),
                "symbol": base_token.get("symbol"),
                "liquidityUsd": liquidity_usd,
                "transactionsLastHour": txns_h1
            })
    return selected_tokens

# Filters for new tokens
def filter_new_tokens(detailed_data):
    selected_tokens = []
    MIN_LIQUIDITY_USD = 5000
    MAX_TXNS_LAST_HOUR = 1000
    PAIR_AGE_MINUTES = 60
    for pair in detailed_data:
        base_token = pair.get("baseToken", {})
        liquidity = pair.get("liquidity", {})
        txns = pair.get("txns", {})
        pair_created_at = pair.get("pairCreatedAt", 0)

        liquidity_usd = liquidity.get("usd", 0)
        txns_h1 = txns.get("h1", {}).get("buys", 0) + txns.get("h1", {}).get("sells", 0)
        pair_age_minutes = (datetime.now().timestamp() - (pair_created_at / 1000)) / 60

        if (
            liquidity_usd >= MIN_LIQUIDITY_USD
            and txns_h1 <= MAX_TXNS_LAST_HOUR
            and pair_age_minutes <= PAIR_AGE_MINUTES
        ):
            selected_tokens.append({
                "tokenAddress": base_token.get("address"),
                "name": base_token.get("name"),
                "symbol": base_token.get("symbol"),
                "liquidityUsd": liquidity_usd,
                "transactionsLastHour": txns_h1,
                "pairAgeMinutes": pair_age_minutes
            })
    return selected_tokens

# Scoring function for ranking tokens
def calculate_score(token):
    transactions = token.get("transactionsLastHour", 0)
    liquidity = token.get("liquidityUsd", 0)
    age = token.get("pairAgeMinutes", float("inf"))  # Penalize older tokens
    return (transactions * 2) + (liquidity * 0.1) - (age * 0.5)

# Main Execution
latest_boosted_tokens = get_latest_boosted_tokens()
most_boosted_tokens = get_most_boosted_tokens()
new_tokens = get_new_tokens()

# Combine all token addresses
all_token_addresses = set(
    token.get('tokenAddress') for token in (latest_boosted_tokens + most_boosted_tokens + new_tokens)
)

# Fetch detailed data
detailed_data = fetch_detailed_data(list(all_token_addresses))

# Apply individual filters
latest_filtered = filter_latest_boosted_tokens(detailed_data)
most_boosted_filtered = filter_most_boosted_tokens(detailed_data)
new_filtered = filter_new_tokens(detailed_data)

# Sort by score and select top 5 from each category
latest_top_5 = sorted(latest_filtered, key=calculate_score, reverse=True)[:5]
most_boosted_top_5 = sorted(most_boosted_filtered, key=calculate_score, reverse=True)[:5]
new_top_5 = sorted(new_filtered, key=calculate_score, reverse=True)[:5]

# Combine results and remove duplicates
combined_tokens = latest_top_5 + most_boosted_top_5 + new_top_5
unique_tokens = remove_duplicates(combined_tokens)

# Output to JSON
output = {
    "timestamp": datetime.now().isoformat(),
    "tokens": unique_tokens
}

with open("tokens.json", "w") as file:
    json.dump(output, file, indent=4)

print("Final filtered tokens written to tokens.json")
