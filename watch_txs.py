import dontshare as d
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from termcolor import colored  # Import termcolor for colored output
import pytz
import schedule
import json  # Add this import at the top of your file
from CONFIG import *


def fetch_wallet_transactions(wallet_address):
    print(f"Fetching transactions for wallet: {wallet_address}")
    url = f"https://public-api.birdeye.so/v1/wallet/tx_list?wallet={wallet_address}&limit=100"
    headers = {
        "accept": "application/json",
        "X-API-KEY": d.birdeye_api_key,
        "x-chain": "solana"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()
        #print(colored("API Response:", 'yellow', 'on_black'))
        #print(json.dumps(json_response, indent=2))
        if 'success' in json_response and json_response['success'] and 'data' in json_response:
            data = json_response['data']
            if isinstance(data, dict) and 'solana' in data:
                return pd.DataFrame(data['solana'])
    return pd.DataFrame()

def get_token_info(address):
    url = f"https://public-api.birdeye.so/v1/token/get_token_info?address={address}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": d.birdeye_api_key,
        "x-chain": "solana"
    }
    #print(f"Fetching token info for address: {address}")
    response = requests.get(url, headers=headers)
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text[:200]}...")  # Print first 200 chars of response
    
    if response.status_code == 200:
        try:
            json_response = response.json()
            print(f"JSON response: {json.dumps(json_response, indent=2)[:200]}...")
            if json_response.get('success') and 'data' in json_response:
                return json_response['data']
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
    print(f"Failed to get token info for address: {address}")
    return {}


def process_transaction(row, wallet):
    changes = row['balanceChange']
    
    bought = next((c for c in changes if c.get('amount', 0) > 0), None)
    sold = next((c for c in changes if c.get('amount', 0) < 0), None)

    if bought or sold:
        bought_amount = abs(bought['amount']) / 10**bought.get('decimals', 9) if bought else 0
        sold_amount = abs(sold['amount']) / 10**sold.get('decimals', 9) if sold else 0
        
        bought_symbol = bought.get('symbol', 'Unknown') if bought else 'N/A'
        sold_symbol = sold.get('symbol', 'Unknown') if sold else 'N/A'
        
        # Filter out irrelevant transactions
        if (bought_symbol == 'SOL' and bought_amount < 0.01) or (sold_symbol == 'SOL' and sold_amount < 0.01):
            return None
        
        non_sol_token = bought if bought_symbol != 'SOL' else sold
        contract_address = non_sol_token['address'] if non_sol_token else ""
        
        action = "Bought" if bought_symbol != 'SOL' else "Sold"
        amount = bought_amount if bought_symbol != 'SOL' else sold_amount
        token = bought_symbol if bought_symbol != 'SOL' else sold_symbol
        
        print(colored(f"{action} {amount:.4f} {token}", 'green', 'on_black'))
        print(colored(f"https://birdeye.so/token/{contract_address}?chain=solana", 'blue', 'on_black'))
        print(colored(f"https://solscan.io/tx/{row['txHash']}", 'blue', 'on_black'))
        print(colored(f"https://gmgn.ai/sol/address/{wallet}", 'blue', 'on_black'))
        print()  # Add a blank line for readability
        
        return {
            'blockTime': row['blockTime'],
            'contract_address': contract_address,
            'owner': wallet,
            'token_bought': bought_symbol if action == "Bought" else 'N/A',
            'token_sold': sold_symbol if action == "Sold" else 'N/A',
            'bought_amount': bought_amount if action == "Bought" else 0,
            'sold_amount': sold_amount if action == "Sold" else 0,
            'birdeye_link': f"https://birdeye.so/token/{contract_address}?chain=solana",
            'solscan_link': f"https://solscan.io/tx/{row['txHash']}",
            'gmgn_link': f"https://gmgn.ai/sol/address/{wallet}"
        }
    return None

def main():
    wallets_df = pd.read_csv('csvs/ppl_to_follow.csv')
    all_transactions = []
    
    for wallet in wallets_df['wallet_address']:
        #print(f"Fetching transactions for wallet: {wallet}")
        transactions_df = fetch_wallet_transactions(wallet)
        if not transactions_df.empty and 'blockTime' in transactions_df.columns:
            transactions_df['blockTime'] = pd.to_datetime(transactions_df['blockTime'], utc=True)
            recent_time = datetime.now(pytz.utc) - timedelta(minutes=MINUTES_TO_CHECK)
            recent_transactions = transactions_df[transactions_df['blockTime'] >= recent_time]
            
            for _, row in recent_transactions.iterrows():
                try:
                    processed = process_transaction(row, wallet)
                    if processed:
                        all_transactions.append(processed)
                        print(colored("Transaction processed successfully", 'green', 'on_black'))
                except Exception as e:
                    print(colored(f"Error processing transaction: {e}", 'red', 'on_black'))
        
        time.sleep(SLEEP_TIME)
    
    if all_transactions:
        try:
            result_df = pd.DataFrame(all_transactions)
            columns_order = ['blockTime', 'contract_address', 'owner', 'token_bought', 'token_sold', 'bought_amount', 'sold_amount', 'birdeye_link', 'solscan_link', 'gmgn_link']
            result_df = result_df[columns_order]
            # Append to CSV instead of overwriting
            result_df.to_csv('csvs/recenttxs.csv', mode='a', header=False, index=False)  # {{ edit_1 }}
            print(colored("\nRecent transactions appended to recenttxs.csv", 'green', 'on_black'))  # {{ edit_2 }}
        except Exception as e:
            print(colored(f"Error saving transactions to CSV: {e}", 'red', 'on_black'))
    else:
        print(colored("No recent transactions retrieved", 'yellow', 'on_black'))


def run_main():
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")