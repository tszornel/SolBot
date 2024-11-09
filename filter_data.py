'''
this file is going to be dedicated to filtering the data folder and putting them in /Users/md/Dropbox/dev/github/solana-copy-trader/data/filtered
where we will do things like drop duplicates
'''

import os
import pandas as pd

# Define input and output directories
input_dir = "/Users/md/Dropbox/dev/github/solana-copy-trader/data"
output_dir = "/Users/md/Dropbox/dev/github/solana-copy-trader/data/filtered"

# Create output directory if it doesn't exist 
os.makedirs(output_dir, exist_ok=True)

def process_csv(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Drop duplicates, keeping the first occurrence for each unique Owner
    df = df.drop_duplicates(subset=['Owner'], keep='first')
    
    # Sort by USD Value in descending order (optional, but might be useful)
    df = df.sort_values('USD Value', ascending=False)
    
    return df


# Process all CSV files in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".csv"):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)  # Changed this line
        
        print(f"Processing {filename}...")
        processed_df = process_csv(input_path)
        
        # Save the processed dataframe to the output directory
        processed_df.to_csv(output_path, index=False)
        print(f"Saved filtered data to {output_path}")

print("All CSV files have been processed and filtered.")
