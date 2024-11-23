import requests
from datetime import datetime
import json

# Step 1: Fetch the latest tokens
new_tokens_url = 'https://api.dexscreener.com/token-profiles/latest/v1'
response = requests.get(new_tokens_url)
if response.status_code != 200:
    print("Failed to fetch new tokens.")
    exit()

new_tokens = response.json()

# Step 2: Extract token addresses
token_addresses = [token.get('tokenAddress') for token in new_tokens if token.get('tokenAddress')]

# Step 3: Fetch detailed token data
if not token_addresses:
    print("No token addresses found.")
    exit()

detailed_data = []
chunk_size = 30  # API limit or optimal chunk size
for i in range(0, len(token_addresses), chunk_size):
    token_chunk = token_addresses[i:i + chunk_size]
    token_addresses_str = ','.join(token_chunk)
    detailed_data_url = f'https://api.dexscreener.com/latest/dex/tokens/{token_addresses_str}'
    response = requests.get(detailed_data_url)
    if response.status_code == 200:
        detailed_data.extend(response.json().get('pairs', []))

if not detailed_data:
    print("Failed to fetch detailed token data or no data available.")
    exit()

# Step 4: Define relaxed filters for early detection
MIN_LIQUIDITY_USD = 5000  # Minimum initial liquidity
MAX_LIQUIDITY_USD = 200000  # Avoid mature coins
MIN_TXNS_LAST_HOUR = 5  # Detect coins with very early activity
MAX_TXNS_LAST_HOUR = 200  # Avoid overly active coins (already pumped)
MAX_VOLUME_LIQUIDITY_RATIO = 10  # Looser ratio for higher activity coins
MIN_PRICE_CHANGE = -10  # Allow for steady or slightly declining coins
MAX_PRICE_CHANGE = 50  # Avoid coins that already show massive pumps
PAIR_AGE_MINUTES = 15  # Slightly increased age window

# Step 5: Filter new tokens
selected_tokens = []

for pair in detailed_data:
    base_token = pair.get('baseToken', {})
    liquidity = pair.get('liquidity', {})
    txns = pair.get('txns', {})
    price_change = pair.get('priceChange', {})
    volume = pair.get('volume', {})
    pair_created_at = pair.get('pairCreatedAt', 0)

    # Extract key metrics
    liquidity_usd = liquidity.get('usd', 0)
    txns_h1 = txns.get('h1', {}).get('buys', 0) + txns.get('h1', {}).get('sells', 0)
    price_change_h1 = price_change.get('h1', 0)
    pair_age_minutes = (datetime.now().timestamp() - (pair_created_at / 1000)) / 60
    volume_liquidity_ratio = volume.get('h24', 0) / liquidity_usd if liquidity_usd else float('inf')

    # Relaxed filters
    if (
        MIN_LIQUIDITY_USD <= liquidity_usd <= MAX_LIQUIDITY_USD
        and MIN_TXNS_LAST_HOUR <= txns_h1 <= MAX_TXNS_LAST_HOUR
        and MIN_PRICE_CHANGE <= price_change_h1 <= MAX_PRICE_CHANGE
        and volume_liquidity_ratio <= MAX_VOLUME_LIQUIDITY_RATIO
        and pair_age_minutes <= PAIR_AGE_MINUTES
    ):
        selected_tokens.append({
            "tokenAddress": base_token.get('address'),
            "name": base_token.get('name'),
            "symbol": base_token.get('symbol'),
            "liquidityUsd": liquidity_usd,
            "transactionsLastHour": txns_h1,
            "priceChangeH1": price_change_h1,
            "pairAgeMinutes": pair_age_minutes
        })

# Step 6: Output for trading bot
output = {
    "timestamp": datetime.now().isoformat(),
    "tokens": selected_tokens
}

# Save output to a JSON file for the trading bot
with open("selected_new_tokens.json", "w") as file:
    json.dump(output, file, indent=4)

print("New tokens sent to trading bot:")
for token in selected_tokens:
    print(f"Token: {token['name']} ({token['symbol']}), Liquidity: ${token['liquidityUsd']}, Age: {token['pairAgeMinutes']} minutes")
