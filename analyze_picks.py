import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import dontshare as d
import pandas_ta as ta
from termcolor import cprint
from CONFIG import *
import re

# Definimos BASE_URL aquí
BASE_URL = "https://public-api.birdeye.so/defi"


def calculate_sma(df, period):
    return df['c'].rolling(window=period).mean().iloc[-1]


def find_urls(text):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return url_pattern.findall(text)

def token_overview(address):
    #print(f'Checking token overview for {address}')
    BASE_URL = "https://public-api.birdeye.so/defi"
    overview_url = f"{BASE_URL}/token_overview?address={address}"
    #print(f'URL: {overview_url}')
    headers = {"X-API-KEY": KEY}

    response = requests.get(overview_url, headers=headers)
    #print(f"Token overview response: {response.status_code}")
    result = {}

    if response.status_code == 200:
        overview_data = response.json().get('data', {})
        #print(f'Overview data: {overview_data}')
        
        #print(f"Complete overview data for {address}:")
        # for key, value in overview_data.items():
        #     print(f"{key}: {value}")

        buy1h = overview_data.get('buy1h', 0)
        sell1h = overview_data.get('sell1h', 0)
        trade1h = buy1h + sell1h

        result['buy1h'] = buy1h
        result['sell1h'] = sell1h
        result['trade1h'] = trade1h

        total_trades = trade1h
        buy_percentage = (buy1h / total_trades * 100) if total_trades else 0
        sell_percentage = (sell1h / total_trades * 100) if total_trades else 0
        result['buy_percentage'] = buy_percentage
        result['sell_percentage'] = sell_percentage

        result['minimum_trades_met'] = True if trade1h >= MIN_TRADES_LAST_HOUR else False

        price_changes = {k: v for k, v in overview_data.items() if 'priceChange' in k}
        result['priceChangesXhrs'] = price_changes

        # Find the worst drop
        worst_drop = min(price_changes.values(), key=lambda x: x if x is not None else float('inf'))
        rug_pull = worst_drop < MAX_DD
        
        print(f'this is the data: {price_changes} rug pull: {rug_pull}')
        if rug_pull:
            cprint(f'rug pull detected: worst drop {worst_drop:.2f}% (MAX_DD: {MAX_DD}%) for {address} so dropping it', 'red')
            return None  # Return None to indicate a rug pull
        else:
            result['rug_pull'] = False

        unique_wallet24h = overview_data.get('uniqueWallet24h', 0)
        v24USD = overview_data.get('v24hUSD', 0)
        watch = overview_data.get('watch', 0)
        view24h = overview_data.get('view24h', 0)
        liquidity = overview_data.get('liquidity', 0)
        mc = overview_data.get('mc', 0)

        result.update({
            'uniqueWallet24h': unique_wallet24h,
            'v24USD': v24USD,
            'watch': watch,
            'view24h': view24h,
            'liquidity': liquidity,
            'mc': mc
        })

        extensions = overview_data.get('extensions', {})
        description = extensions.get('description', '') if extensions else ''
        urls = find_urls(description)
        links = []
        for url in urls:
            if 't.me' in url:
                links.append({'telegram': url})
            elif 'twitter.com' in url:
                links.append({'twitter': url})
            elif 'youtube' not in url:
                links.append({'website': url})

        result['description'] = links

        return result
    else:
        print(f"Couldn't get token overview for {address}: HTTP status code {response.status_code}")
        return None

def check_price_changes(overview, address, MAX_DD):
    price_changes = overview.get('priceChangesXhrs', {})
    #print(f"************************** Price changes: {price_changes}")
    
    for key, price_change in price_changes.items():
        if price_change is None:
            continue
        
        if price_change < MAX_DD:
            #cprint(f"Warning! {address} has a big drop in {key}: {price_change:.2f}%", 'white', 'on_red')
            return False
    
    #cprint(f"Great! {address} doesn't have extreme drops", 'white', 'on_green')
    return True

def get_time_range():
    now = datetime.now()
    ten_days_earlier = now - timedelta(days=10)
    time_to = int(now.timestamp())
    time_from = int(ten_days_earlier.timestamp())
    return time_from, time_to

def get_ohlcv_data(contract_address, timeframe):
    time_from, time_to = get_time_range()
    
    # Convertir timeframe a formato aceptado por la API
    if timeframe == '4h':
        timeframe = '4H'
    # No necesitamos cambiar '15m' ya que ya está en el formato correcto
    
    url = f"https://public-api.birdeye.so/defi/ohlcv?address={contract_address}&type={timeframe}&time_from={time_from}&time_to={time_to}"
    headers = {
        "X-API-KEY": KEY,
        "accept": "application/json",
        "x-chain": "solana"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        #print(f"OHLCV ({timeframe}) response: {response.status_code}")
        
        json_response = response.json()
        items = json_response.get('data', {}).get('items', [])
        
        if not items:
            #print(f"No se encontraron datos OHLCV para {contract_address} ({timeframe})")
            return None
        
        df = pd.DataFrame(items)
        df['timestamp'] = pd.to_datetime(df['unixTime'], unit='s')
        df = df.sort_values('timestamp')
        
        if len(df) < 40:
            rows_to_add = 40 - len(df)
            first_row_replicated = pd.concat([df.iloc[0:1]] * rows_to_add, ignore_index=True)
            df = pd.concat([first_row_replicated, df], ignore_index=True)
        
        df['sma_20'] = ta.sma(df['c'], length=20)
        df['rsi'] = ta.rsi(df['c'], length=14)
        df['sma_40'] = ta.sma(df['c'], length=40)
        
        return df
    except requests.exceptions.RequestException as e:
        #print(f"Error al obtener datos OHLCV para {contract_address} ({timeframe}): {e}")
        #print(f"URL de la solicitud: {url}")
        #print(f"Respuesta del servidor: {response.text if 'response' in locals() else 'No response'}")
        return None

def get_current_price(contract_address):
    url = f"https://public-api.birdeye.so/defi/price?address={contract_address}"
    headers = {
        "X-API-KEY": KEY,  # Aquí también usamos KEY de CONFIG
        "accept": "application/json",
        "x-chain": "solana"
    }
    #print(f"Requesting current price for {contract_address}")
    #print(f"URL: {url}")
    response = requests.get(url, headers=headers)
    #print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        #print("Price data fetched successfully")
        return data.get('data', {}).get('value')
    else:
        #print(f"Error fetching current price for {contract_address}: {response.status_code}")
        return None
def test_known_token():
    known_token = "So11111111111111111111111111111111111111112"  # SOL token address
    #print(f"Testing known token: {known_token}")
    ohlcv_data = get_ohlcv_data(known_token, TIMEFRAME_FOR_SMA)
    if ohlcv_data is not None and not ohlcv_data.empty:
        #print(f"OHLCV data fetched successfully. Shape: {ohlcv_data.shape}")
        current_price = get_current_price(known_token)
        if current_price is not None:
            #print("Known token test successful!")
            #print(f"OHLCV data shape: {ohlcv_data.shape}")
            #print(f"Current price: {current_price}")
            return True
    #print("Known token test failed.")
    return False

def token_security_info(address):
    url = f"{BASE_URL}/token_security?address={address}"
    headers = {"X-API-KEY": KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        #print(f"Security info fetched successfully for {address}")
        return response.json()['data']
    else:
        #cprint(f"Error getting security info for {address}: {response.status_code}", 'red')
        return None

def analyze_picks():
    if not test_known_token():
        return

    df = pd.read_csv('csvs/recenttxs.csv')
    print(f'\n=== Time Filter Debug ===')
    print(f'Original df length: {len(df)}')
    
    # Convert blockTime to UTC datetime
    df['blockTime'] = pd.to_datetime(df['blockTime']).dt.tz_convert('UTC').dt.tz_localize(None)
    cutoff_time = (pd.Timestamp.now(tz='UTC') - pd.Timedelta(minutes=MINUTES_TO_CHECK)).tz_localize(None)
    
    print(f'Current UTC time: {pd.Timestamp.now(tz="UTC")}')
    print(f'Cutoff time (UTC): {cutoff_time}')
    print(f'Minutes to check: {MINUTES_TO_CHECK}')
    print(f'Sample of blockTimes:\n{df["blockTime"].head()}')
    
    df = df[df['blockTime'] >= cutoff_time]
    print(f'Filtered df length: {len(df)}')
    print(f'=== End Time Filter Debug ===\n')

    results = []
    trending_tokens = set()
    
    for _, row in df.iterrows():
        address = row['contract_address']
        owner = row['owner']
        birdeye_url = row.get('birdeye_url', f"https://birdeye.so/token/{address}")
        
        try:
            cprint(f"\nAnalyzing token: {address}", 'cyan')

            if address in DO_NOT_TRADE_LIST:
                cprint(f"Warning! {address} is in the do not trade list", 'white', 'on_red')
                continue

            security_info = token_security_info(address)
            if security_info is None:
                cprint(f"Couldn't get security info for {address}", 'red')
                continue

            if security_info.get('freezeable') == True:
                cprint(f"Warning! {address} is freezable", 'white', 'on_red')
                continue
            else:
                cprint(f"Good! {address} is not freezable", 'white', 'on_green')
                pass

            top_10_percent = security_info.get('top10HolderPercent', 0)
            #print(f"Top 10 percent: {top_10_percent} MAX: {TOP_10PERC_MAX}")
            if top_10_percent > TOP_10PERC_MAX:
                cprint(f"Warning! {address} has high concentration in top 10 holders: {top_10_percent:.2%}", 'white', 'on_red')
                continue
            else:
                cprint(f"Great! {address} has good distribution in top 10 holders: {top_10_percent:.2%}", 'white', 'on_green')
                pass

            #print(f"Mutable metadata: {security_info.get('mutableMetadata')}")
            if security_info.get('mutableMetadata') == True:
                cprint(f"Warning! {address} has mutable metadata", 'white', 'on_red')
                continue
            else:
                cprint(f"Perfect! {address} doesn't have mutable metadata", 'white', 'on_green')
                pass

            overview = token_overview(address)
            if overview is None:
                cprint(f"Couldn't get overview for {address}", 'red')
                continue  # Skip this token if it's a potential rug pull

            if not check_price_changes(overview, address, MAX_DD):
                cprint(f"Warning! {address} has extreme price drops", 'white', 'on_red')
                continue

            print(f"Trades in the last hour: {overview['trade1h']} MIN: {MIN_TRADES_LAST_HOUR}")
            if overview['trade1h'] >= MIN_TRADES_LAST_HOUR:
                cprint(f"Great! {address} has enough trades in the last hour: {overview['trade1h']}", 'white', 'on_green')
                pass
            else:
                cprint(f"Not enough trades for {address}: {overview['trade1h']}", 'white', 'on_red')
                continue

            print(f"Market cap: {overview['mc']} MAX: {MAX_MARKET_CAP}")
            if overview['mc'] <= MAX_MARKET_CAP:
                cprint(f"Good! {address} has an acceptable market cap: {overview['mc']}", 'white', 'on_green')
                pass
            else:
                cprint(f"Market cap too high for {address}: {overview['mc']}", 'white', 'on_red')
                continue

            print(f"Liquidity: {overview['liquidity']} MIN: {MIN_LIQUIDITY}")
            if overview['liquidity'] >= MIN_LIQUIDITY:
                cprint(f"Great! {address} has good liquidity: {overview['liquidity']}", 'white', 'on_green')
                pass
            else:
                cprint(f"Not enough liquidity for {address}: {overview['liquidity']}", 'white', 'on_red')
                continue

            print(f"Unique wallets: {overview['uniqueWallet24h']} MIN: {UNIQUE_WALLETS}")
            if overview['uniqueWallet24h'] >= UNIQUE_WALLETS:
                cprint(f"Cool! {address} has many unique wallets: {overview['uniqueWallet24h']}", 'white', 'on_green')
                pass
            else:
                cprint(f"Not enough unique wallets for {address}: {overview['uniqueWallet24h']}", 'white', 'on_red')
                continue

            ohlcv_data_4h = get_ohlcv_data(address, TIMEFRAME_FOR_SMA)
            ohlcv_data_15m = get_ohlcv_data(address, '15m')
            if ohlcv_data_4h is not None and not ohlcv_data_4h.empty and ohlcv_data_15m is not None and not ohlcv_data_15m.empty:
                current_price = get_current_price(address)
                if current_price is not None:
                    sma_20_4h = calculate_sma(ohlcv_data_4h, 20)
                    sma_20_15m = calculate_sma(ohlcv_data_15m, 20)
                    is_over_sma_4h = current_price > sma_20_4h
                    is_over_sma_15m = current_price > sma_20_15m
                    print(f"Current price: {current_price:.6f} > SMA20 (4h): {sma_20_4h:.6f}")
                    print(f"Current price: {current_price:.6f} > SMA20 (15m): {sma_20_15m:.6f}")
                    if is_over_sma_4h and is_over_sma_15m:
                        cprint(f"Awesome! {address} - Current price: {current_price:.6f} > SMA20 (4h): {sma_20_4h:.6f} and SMA20 (15m): {sma_20_15m:.6f}", 'white', 'on_green')
                        # cprint(f"Check the token on Birdeye: {birdeye_url}", 'white', 'on_green')
                        trending_tokens.add((address, birdeye_url, owner))
                    elif is_over_sma_4h:
                        cprint(f"Almost... {address} - Current price: {current_price:.6f} > SMA20 (4h): {sma_20_4h:.6f}, but <= SMA20 (15m): {sma_20_15m:.6f}", 'yellow')
                        pass
                    else:
                        cprint(f"Nope... {address} - Current price: {current_price:.6f} <= SMA20 (4h): {sma_20_4h:.6f}", 'yellow')
                        pass
                else:
                    cprint(f"Couldn't get current price for {address}", 'red')
                    pass
            else:
                cprint(f"Couldn't get OHLCV data for {address}", 'red')
                pass

        except Exception as e:
            cprint(f"Error processing {address}: {str(e)}", 'red')
            pass
    
    # print the list of trending tokens 
    for token in trending_tokens:
        cprint(f'trending token found: {token[0]}', 'white', 'on_green')

    if trending_tokens:
        print(f'saving to csv...')
        trending_df = pd.DataFrame(trending_tokens, columns=['contract_address', 'birdeye_url', 'owner'])
        trending_df.to_csv('csvs/trending_tokens.csv', index=False)
        #print(f"\nSuccess! Trending tokens saved to trending_tokens.csv")
        #print(f"Number of trending tokens: {len(trending_tokens)}")
    else:
        #print("\nNone... No trending tokens found.")
        pass

# if __name__ == "__main__":
#     try:
#         analyze_picks()
#     except KeyboardInterrupt:
#         print("\nUser interrupted the script. Exiting...")
#     except Exception as e:
#         print(f"An error occurred: {e}")








