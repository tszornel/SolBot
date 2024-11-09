import pandas as pd

# Load the CSV files
bots_df = pd.read_csv('/Users/md/Dropbox/dev/github/solana-copy-trader/bots_to_study.csv')
ppl_df = pd.read_csv('/Users/md/Dropbox/dev/github/solana-copy-trader/ppl_to_follow.csv')

# Define a function to extract the wallet address from the URL
def extract_wallet_address(url):
    return url.split('/')[-1]


# Add the wallet_address column to both DataFrames
bots_df['wallet_address'] = bots_df['URL'].apply(extract_wallet_address)
ppl_df['wallet_address'] = ppl_df['URL'].apply(extract_wallet_address)

# Add Solscan link to both DataFrames
solscan_base_url = "https://solscan.io/account/"
bots_df['solscan_link'] = solscan_base_url + bots_df['wallet_address']
ppl_df['solscan_link'] = solscan_base_url + ppl_df['wallet_address']

# Reorganize columns: move wallet_address and solscan_link to the end
bots_df = bots_df[['URL', 'wallet_address', 'solscan_link', 'Notes']]  # Adjust as necessary
ppl_df = ppl_df[['URL', 'wallet_address', 'solscan_link', 'Notes']]  # Adjust as necessary

# Save the updated DataFrames back to CSV
bots_df.to_csv('/Users/md/Dropbox/dev/github/solana-copy-trader/bots_to_study.csv', index=False)
ppl_df.to_csv('/Users/md/Dropbox/dev/github/solana-copy-trader/ppl_to_follow.csv', index=False)

