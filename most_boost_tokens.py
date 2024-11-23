import requests
from datetime import datetime
import json

# Step 1: Fetch the most boosted tokens
boosted_tokens_url = 'https://api.dexscreener.com/token-boosts/top/v1'
response = requests.get(boosted_tokens_url)
if response.status_code != 200:
    print("Failed to fetch most boosted tokens.")
    exit()

boosted_tokens = response.json()

# Step 2: Extract token addresses and boosts
token_addresses = []
token_boosts = {}

for token in boosted_tokens:
    token_address = token.get('tokenAddress')
    active_boost = token.get('boosts', {}).get('active', 0)
    if token_address:
        token_addresses.append(token_address)
        token_boosts[token_address] = active_boost

if not token_addresses:
    print("No token addresses found.")
    exit()

# Step 3: Fetch detailed token data in chunks (max 30 addresses per request)
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

detailed_data = fetch_detailed_data(token_addresses)

# Step 4: Define filters for most boosted tokens
MIN_LIQUIDITY_USD = 10000      # Moderate liquidity for boosted tokens
MIN_MARKET_CAP = 50000         # Higher market cap for more stability
MIN_TXNS_LAST_HOUR = 50        # Higher transactions for boosted tokens
MIN_PRICE_CHANGE_H1 = 2        # Moderate price increase
MAX_PRICE_CHANGE_H1 = 300       # Allow higher price change for pumps
MAX_VOLUME_LIQUIDITY_RATIO = 100 # To avoid over-traded tokens
MIN_BOOST_ACTIVE = 0         # High boost activity threshold

# Step 5: Filter tokens
selected_tokens = []

for pair in detailed_data:
    base_token = pair.get("baseToken", {})
    liquidity = pair.get("liquidity", {})
    txns = pair.get("txns", {})
    price_change = pair.get("priceChange", {})
    volume = pair.get("volume", {})
    token_address = base_token.get("address")
    
    # Extract boost value
    total_boost = token_boosts.get(token_address, 0)

    # Extract key metrics
    liquidity_usd = liquidity.get("usd", 0)
    market_cap = pair.get("marketCap", 0)
    txns_h1 = txns.get("h1", {}).get("buys", 0) + txns.get("h1", {}).get("sells", 0)
    txns_h6 = txns.get("h6", {}).get("buys", 0) + txns.get("h6", {}).get("sells", 0)
    price_change_h1 = price_change.get("h1", 0)
    price_change_h6 = price_change.get("h6", 0)
    volume_h1 = volume.get("h1", 0)
    volume_h6 = volume.get("h6", 0)
    volume_liquidity_ratio = volume.get("h24", 0) / liquidity_usd if liquidity_usd else float('inf')

    # Debugging: Log token metrics
    print(f"Token: {base_token.get('name')} ({base_token.get('symbol')})")
    print(f"Liquidity USD: {liquidity_usd}, Market Cap: {market_cap}, "
          f"Transactions H1: {txns_h1}, Transactions H6: {txns_h6}, "
          f"Price Change H1: {price_change_h1}, Boosts: {total_boost}, "
          f"Volume/Liquidity Ratio: {volume_liquidity_ratio}")

    # Apply filters
    if (
        liquidity_usd >= MIN_LIQUIDITY_USD
        and market_cap >= MIN_MARKET_CAP
        and txns_h1 >= MIN_TXNS_LAST_HOUR
        and volume_h1 >= 0.5 * volume_h6  # Recent volume should remain significant
        #and price_change_h1 >= 0.25 * price_change_h6  # Allow for steady/slightly declining momentum
        #and price_change_h1 >= MIN_PRICE_CHANGE_H1  # Ensure minimum price activity
        and volume_liquidity_ratio <= MAX_VOLUME_LIQUIDITY_RATIO
        and total_boost >= MIN_BOOST_ACTIVE
    ):
        selected_tokens.append({
            "tokenAddress": token_address,
            "name": base_token.get("name"),
            "symbol": base_token.get("symbol"),
            "marketCap": market_cap,
            "liquidityUsd": liquidity_usd,
            "transactionsLastHour": txns_h1,
            "priceChangeH1": price_change_h1,
            "boosts": total_boost
        })


# Step 6: Output filtered tokens
output = {
    "timestamp": datetime.now().isoformat(),
    "tokens": selected_tokens
}

with open("selected_tokens_most_boosted.json", "w") as file:
    json.dump(output, file, indent=4)

print("Filtered tokens written to selected_tokens_most_boosted.json")
