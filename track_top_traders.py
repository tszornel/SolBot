import dontshare as d
import pandas as pd
import requests
import time
from datetime import datetime

def fetch_wallet_tokens(wallet_address):
    url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={wallet_address}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": d.birdeye_api_key
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()
        
        if 'data' in json_response and 'items' in json_response['data']:
            df = pd.DataFrame(json_response['data']['items'])
            
            if all(col in df.columns for col in ['address', 'symbol', 'uiAmount', 'valueUsd']):
                df = df[['address', 'symbol', 'uiAmount', 'valueUsd']]
                df = df.rename(columns={'address': 'Mint Address', 'symbol': 'Token Symbol', 'uiAmount': 'Amount', 'valueUsd': 'USD Value'})
                print(df)  # Print the DataFrame for the wallet tokens
                return df
            else:
                print(f"Missing columns for wallet {wallet_address}")
                return pd.DataFrame()
        else:
            print(f"No data available for wallet {wallet_address}")
            return pd.DataFrame()
    else:
        print(f"Failed to retrieve token list for wallet {wallet_address}")
        return pd.DataFrame()
    
def main():
    # Read wallet addresses from ppl_to_follow.csv
    wallets_df = pd.read_csv('csvs/ppl_to_follow.csv')
    
    all_tokens = []
    
    for wallet in wallets_df['wallet_address']:
        tokens_df = fetch_wallet_tokens(wallet)
        if not tokens_df.empty:
            print(tokens_df)  # Print the DataFrame for the tokens retrieved
            tokens_df['Wallet'] = wallet
            all_tokens.append(tokens_df)
        
        # Add a delay to avoid rate limiting
        time.sleep(1)
    
    if all_tokens:
        result_df = pd.concat(all_tokens, ignore_index=True)
        result_df.to_csv('csvs/wallet_tokens.csv', index=False)
        print("Token data saved to wallet_tokens.csv")
        
        # Analyze top traded tokens
        top_tokens = result_df.groupby('Token Symbol').agg({
            'USD Value': 'sum',
            'Wallet': 'count'
        }).reset_index()

    top_tokens = top_tokens[~top_tokens['Token Symbol'].isin(['SOL', 'USDC'])]  # Ignore SOL and USDC
    top_tokens = top_tokens[top_tokens['Wallet'] >= 2]  # Filter for tokens with 2 or more wallets
    top_tokens = top_tokens.sort_values('USD Value', ascending=False)  # Sort by total USD value
    top_tokens = top_tokens.rename(columns={'Wallet': 'Wallet Count'})
    
    # Generate summary
    current_time = datetime.now().strftime("%m/%d %H")
    summary = f"Top Traded Tokens as of {current_time}:\n\n"

    for _, row in top_tokens.iterrows():  # Show all qualifying tokens
        summary += f"{row['Token Symbol']}:\n"
        summary += f"  Total USD Value: ${row['USD Value']:,.2f}\n"
        summary += f"  Number of Wallets: {row['Wallet Count']}\n\n"
    
        # Save summary to top_memes.txt
        with open('top_memes.txt', 'w') as f:  # Change file name to top_memes.txt
            f.write(summary)
        
        print("Top traded tokens summary saved to top_memes.txt")
    else:
        print("No token data retrieved")

if __name__ == "__main__":
    main()