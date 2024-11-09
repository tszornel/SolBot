

from CONFIG import *

from termcolor import colored, cprint 

import requests
import pandas as pd
import pprint
import re as reggie
import dontshare as d
import json
import numpy as np
import time


# API Key from your 'dontshare' file
API_KEY = d.birdeye_api_key

sample_address = "2yXTyarttn2pTZ6cwt4DqmrRuBw1G7pmFv9oT6MStdKP"

BASE_URL = "https://public-api.birdeye.so/defi"

def token_price(address):
    API_KEY = d.birdeye_api_key
    url = f"https://public-api.birdeye.so/defi/price?address={address}"
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    price_data = response.json()
    
    if price_data['success']:
        return price_data['data']['value']
    else:
        return None
    

def ask_bid(token_mint_address):

    ''' this returns the price '''

    API_KEY = d.birdeye_api_key
    
    url = f"https://public-api.birdeye.so/defi/price?address={token_mint_address}"
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()  # Parse the JSON response
        if 'data' in json_response and 'value' in json_response['data']:
            return json_response['data']['value']  # Return the price value
        else:
            return "Price information not available"  # Return a message if 'data' or 'value' is missing
    else:
        return None  # Return None if there's an error with the API call


def get_token_overview(address):

    '''
    update this function so that i can cache it and not call it as much

    '''
    API_KEY = d.birdeye_api_key
    url = f"https://public-api.birdeye.so/defi/token_overview?address={address}"
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    if response.ok:
        json_response = response.json()
        return json_response['data']
    else:
        # Return empty dict if there's an error
        print(f"Error fetching data for address {address}: {response.status_code}")
        return {}



def get_decimals(token_mint_address):
    import requests
    import base64
    import json
    # Solana Mainnet RPC endpoint
    url = "https://api.mainnet-beta.solana.com/"
    
    headers = {"Content-Type": "application/json"}

    # Request payload to fetch account information
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [
            token_mint_address,
            {
                "encoding": "jsonParsed"
            }
        ]
    })

    # Make the request to Solana RPC
    response = requests.post(url, headers=headers, data=payload)
    response_json = response.json()

    # Parse the response to extract the number of decimals
    decimals = response_json['result']['value']['data']['parsed']['info']['decimals']
    #print(f"Decimals for {token_mint_address[:4]} token: {decimals}")

    return decimals


def fetch_wallet_holdings_nosaving_names(address, token_mint_address):

    API_KEY = d.birdeye_api_key # Assume this is your API key; replace it with the actual one

    # Initialize an empty DataFrame
    df = pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])

    url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={address}"
    headers = {"x-chain": "solana", "X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()

        if 'data' in json_response and 'items' in json_response['data']:
            df = pd.DataFrame(json_response['data']['items'])
            
            try:
                df = df[['address', 'uiAmount', 'valueUsd']]
                df = df.rename(columns={'address': 'Mint Address', 'uiAmount': 'Amount', 'valueUsd': 'USD Value'})
                df = df.dropna()
                df = df[df['USD Value'] > 0.05]
            except KeyError as e:
                cprint(f"Error processing data: {e}. Available columns: {df.columns}", 'white', 'on_red')
                return pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])  # Return an empty DataFrame
        else:
            cprint("No data available in the response.", 'white', 'on_red')
            return pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])  # Return an empty DataFrame
    else:
        cprint(f"Failed to retrieve token list for {address[-3:]}.", 'white', 'on_magenta')
        time.sleep(10)
        return pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])  # Return an empty DataFrame

 
    # drop any row that is on the do not trade list
    # but keep these two tokens 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' and Solana contract address
    
    # Addresses to exclude from the "do not trade list"
    exclude_addresses = ['EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 'So11111111111111111111111111111111111111112']

    # Update the "do not trade list" by removing the excluded addresses
    updated_dont_trade_list = [mint for mint in DO_NOT_TRADE_LIST if mint not in exclude_addresses]

    # Filter the dataframe
    for mint in updated_dont_trade_list:
        df = df[df['Mint Address'] != mint]

    # filter by token mint address
    df = df[df['Mint Address'] == token_mint_address]

    return df


def market_buy(token, amount):

    import requests
    import sys
    import json
    import base64
    from solders.keypair import Keypair
    from solders.transaction import VersionedTransaction
    from solana.rpc.api import Client
    from solana.rpc.types import TxOpts
    import dontshare as d 

    KEY = Keypair.from_base58_string(d.sol_key)
    SLIPPAGE = 5000 # 5000 is 50%, 500 is 5% and 50 is .5%
    #QUOTE_TOKEN = "So11111111111111111111111111111111111111112"
    QUOTE_TOKEN = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # usdc

    http_client = Client(d.ankr_key)
    #http_client = Client("https://rpc.ankr.com/solana/b0d038027b60cf79aba1de4eb52d9b0c0df3a0b7066a68ebfb3edb43be7138ee")


    quote = requests.get(f'https://quote-api.jup.ag/v6/quote?inputMint={QUOTE_TOKEN}&outputMint={token}&amount={amount}&slippageBps={SLIPPAGE}').json()
    #print(quote)

    txRes = requests.post('https://quote-api.jup.ag/v6/swap',headers={"Content-Type": "application/json"}, data=json.dumps({"quoteResponse": quote, "userPublicKey": str(KEY.pubkey()) })).json()
    #print(txRes)
    swapTx = base64.b64decode(txRes['swapTransaction'])
    #print(swapTx)
    tx1 = VersionedTransaction.from_bytes(swapTx)
    tx = VersionedTransaction(tx1.message, [KEY])
    txId = http_client.send_raw_transaction(bytes(tx), TxOpts(skip_preflight=True)).value
    print(f"https://solscan.io/tx/{str(txId)}")



def market_sell(QUOTE_TOKEN, amount):

    print('market sell starting')
    import requests
    import sys
    import json
    import base64
    from solders.keypair import Keypair
    from solders.transaction import VersionedTransaction
    from solana.rpc.api import Client
    from solana.rpc.types import TxOpts
    import dontshare as d 

    KEY = Keypair.from_base58_string(d.sol_key) # SOLANA PRIVATE KEY
    SLIPPAGE = 5000 # 5000 is 50%, 500 is 5% and 50 is .5%
    #QUOTE_TOKEN = "So11111111111111111111111111111111111111112"
    # QUOTE_TOKEN = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" # usdc

    # token would be usdc for sell orders cause we are selling
    token =  "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

    print(f'selling {amount} of {QUOTE_TOKEN}')

    http_client = Client(d.ankr_key) #says ankr key but really helius
    #http_client = "https://api.mainnet-beta.solana.com/"
    #http_client = Client("https://rpc.ankr.com/solana/b0d038027b60cf79aba1de4eb52d9b0c0df3a0b7066a68ebfb3edb43be7138ee")


    quote = requests.get(f'https://quote-api.jup.ag/v6/quote?inputMint={QUOTE_TOKEN}&outputMint={token}&amount={amount}&slippageBps={SLIPPAGE}').json()
    #print(quote)
    txRes = requests.post('https://quote-api.jup.ag/v6/swap',headers={"Content-Type": "application/json"}, data=json.dumps({"quoteResponse": quote, "userPublicKey": str(KEY.pubkey()) })).json()
    #print(txRes)
    swapTx = base64.b64decode(txRes['swapTransaction'])
    #print(swapTx)
    tx1 = VersionedTransaction.from_bytes(swapTx)
    #print(tx1)
    tx = VersionedTransaction(tx1.message, [KEY])
    #print(tx)
    txId = http_client.send_raw_transaction(bytes(tx), TxOpts(skip_preflight=True)).value
    print(f"https://solscan.io/tx/{str(txId)}")


def kill_switch(token_mint_address):

    print(f'kill switch for {token_mint_address[:4]}')

    # if time is on the 5 minute do the balance check, if not grab from data/current_position.csv
    balance = fetch_wallet_holdings_nosaving_names(MY_ADDRESS, token_mint_address)
    try:
        balance = balance['Amount'].iloc[0]
        print(f'balance: {balance}')
    except:
        print(f'no balance for {token_mint_address[:4]}')
        balance = 0
        return
    
    # save to data/current_position.csv w/ pandas
    sell_size = balance 
    decimals = 0
    decimals = get_decimals(token_mint_address)
    #print(f'for {token_mint_address[:4]} decimals is {decimals}')

    sell_size = int(sell_size * 10 **decimals)
    
    #print(f'bal: {balance} price: {price} usdVal: {usd_value} TP: {tp} sell size: {sell_size} decimals: {decimals}')

    while sell_size > 0:

        # log this mint address to a file and save as a new line, keep the old lines there, so it will continue to grow this file is called data/closed_positions.txt
        # only add it to the file if it's not already there
        with open(CLOSED_POSITIONS_TXT, 'r') as f:
            lines = [line.strip() for line in f.readlines()]  # Strip the newline character from each line
            if token_mint_address not in lines:  # Now the comparison should work as expected
                with open(CLOSED_POSITIONS_TXT, 'a') as f:
                    f.write(token_mint_address + '\n')

        print(f'closing {token_mint_address[:4]}')
        try:

            market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_green')
            time.sleep(1)
            market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_green')
            time.sleep(1)
            market_sell(token_mint_address, sell_size)
            cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_green')
            time.sleep(15)
            
        except:
            cprint('order error.. trying again', 'white', 'on_red')
            # time.sleep(7)

        # if time is on the 5 minute do the balance check, if not grab from data/current_position.csv
        balance = fetch_wallet_holdings_nosaving_names(MY_ADDRESS, token_mint_address)
        try:
            balance = balance['Amount'].iloc[0]
            print(f'balance: {balance}')
        except:
            print(f'no balance for {token_mint_address[:4]}')
            balance = 0
            return

        sell_size = balance 
        # decimals = 0
        # decimals = get_decimals(token_mint_address)
        #print(f'xxxxxxxxx for {token_mint_address[:4]} decimals is {decimals}')
        sell_size = int(sell_size * 10 **decimals)
        print(f'sell size: {sell_size}')


    else:
        #print(f'for {token_mint_address[:4]} value is {usd_value} and tp is {tp} so not closing...')
        print('looks like its been closed')
        #time.sleep(10)


def get_names_nosave(df):
    names = []  # Lista para guardar los nombres recolectados
    low_volume_tokens = []  # Lista para direcciones de tokens con bajo volumen de trading

    for index, row in df.iterrows():
        token_mint_address = row['Mint Address']
        token_data = get_token_overview(token_mint_address)

        # Extraer el nombre del token usando la clave 'name' de token_data
        token_name = token_data.get('name', 'N/A')  # Usar 'N/A' si no se proporciona el nombre
        names.append(token_name)
        
        # Verificar el volumen de trading en los últimos 30 minutos
        trade30m = token_data.get('trade30m', 0)
        print(f'{token_name} has {trade30m} trades in the last 30 mins')
        if trade30m < MIN_TRADES_30M_ONCE_IN_POSITION:
            low_volume_tokens.append(token_mint_address)

    # Verificar si la columna 'name' ya existe, actualizarla si es así, de lo contrario insertarla
    if 'name' in df.columns:
        df['name'] = names  # Actualizar la columna 'name' existente
    else:
        df.insert(0, 'name', names)  # Insertar 'name' como la primera columna

    # Eliminar las columnas 'Mint Address' y 'Amount'
    df.drop('Mint Address', axis=1, inplace=True)
    df.drop('Amount', axis=1, inplace=True)

    print(f'low_volume_tokens: {low_volume_tokens}')
    return df, low_volume_tokens


def get_names(df):
    names = []  # List to hold the collected names

    for index, row in df.iterrows():
        token_mint_address = row['contract_address']
        token_data = get_token_overview(token_mint_address)
        time.sleep(2)
        
        # Extract the token name using the 'name' key from the token_data
        token_name = token_data.get('name', 'N/A')  # Use 'N/A' if name isn't provided
        print(f'Name for {token_mint_address[:4]}: {token_name}')
        names.append(token_name)
    
    # Check if 'name' column already exists, update it if it does, otherwise insert it
    if 'name' in df.columns:
        df['name'] = names  # Update existing 'name' column
    else:
        df.insert(0, 'name', names)  # Insert 'name' as the first column

    # Save df to vibe_check.csv
    df.to_csv(READY_TO_BUY_CSV, index=False)
    
    return df

def fetch_wallet_holdings_og(address):

    API_KEY = d.birdeye_api_key # Assume this is your API key; replace it with the actual one

    # Initialize an empty DataFrame
    df = pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])

    url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={address}"
    headers = {"x-chain": "solana", "X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        json_response = response.json()

        if 'data' in json_response and 'items' in json_response['data']:
            df = pd.DataFrame(json_response['data']['items'])
            
            try:
                df = df[['address', 'uiAmount', 'valueUsd']]
                df = df.rename(columns={'address': 'Mint Address', 'uiAmount': 'Amount', 'valueUsd': 'USD Value'})
                df = df.dropna()
                df = df[df['USD Value'] > 0.05]
            except KeyError as e:
                cprint(f"Error processing data: {e}. Available columns: {df.columns}", 'white', 'on_red')
                return pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])  # Return an empty DataFrame
        else:
            cprint("No data available in the response.", 'white', 'on_red')
            return pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])  # Return an empty DataFrame
    else:
        cprint(f"Failed to retrieve token list for {address[-3:]}.", 'white', 'on_magenta')
        time.sleep(10)
        return pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])  # Return an empty DataFrame

 
    # drop any row that is on the do not trade list
    # but keep these two tokens 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' and Solana contract address
    
    # Addresses to exclude from the "do not trade list"
    exclude_addresses = ['EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 'So11111111111111111111111111111111111111112']

    # Update the "do not trade list" by removing the excluded addresses
    updated_dont_trade_list = [mint for mint in DO_NOT_TRADE_LIST if mint not in exclude_addresses]

    # Filter the dataframe
    for mint in updated_dont_trade_list:
        df = df[df['Mint Address'] != mint]


    # Print the DataFrame if it's not empty
    if not df.empty:
        
        # Save the filtered DataFrame to a CSV file
        TOKEN_PER_ADDY_CSV = 'filtered_wallet_holdings.csv'  # Define your CSV file name
        df.to_csv(TOKEN_PER_ADDY_CSV, index=False)
        # update the df so Mint_address so it's just the last 2
        
        df2, low_volume_tokens = get_names_nosave(df.copy())

        # remove any low_volumetokens that are in the do not trade list
        low_volume_tokens = [token for token in low_volume_tokens if token not in DO_NOT_TRADE_LIST]

        # for low olume tokens, runkill switch
        for token in low_volume_tokens:
            print(f'low volume token: {token} so killing')
            kill_switch(token)



        #df['Mint Address'] = df['Mint Address'].str[:4]
        # print the df in reverse
        #df2 = df2.iloc[::-1]
        print('')
        #print(df2.tail(20))
        print(df2.head(50))
        # Assuming cprint is a function you have for printing in color
        print('moondev.sol wallet started march 2024')
        cprint(f'** Starting: 200 | Current: ${round(df2["USD Value"].sum(),2)}', 'white', 'on_green')
        print(' ')
        time.sleep(7)
    else:
        # If the DataFrame is empty, print a message or handle it as needed
        cprint("No wallet holdings to display.", 'white', 'on_red')
        time.sleep(30)

    return df



def fetch_wallet_token_single(wallet_address, token_mint_address):
    print(f"Fetching individual token for {token_mint_address[:4]}")
    
    API_KEY = d.birdeye_api_key  # Asegúrate de que esto esté definido
    url = f"https://public-api.birdeye.so/v1/wallet/token_list?wallet={wallet_address}"
    
    headers = {
        "accept": "application/json",
        "x-chain": "solana",
        "X-API-KEY": API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Esto levantará una excepción para códigos de estado HTTP no exitosos
        
        data = response.json()
        
        print("API Response:")
        print(data)  # Imprime la respuesta completa de la API
        
        if 'data' in data and 'items' in data['data']:
            df = pd.DataFrame(data['data']['items'])
            
            print("DataFrame columns:")
            print(df.columns)  # Imprime las columnas del DataFrame
            
            print("DataFrame head:")
            print(df.head())  # Imprime las primeras filas del DataFrame
            
            # Filtra por el token_mint_address específico
            if 'address' in df.columns:
                df = df[df['address'] == token_mint_address]
            elif 'tokenAddress' in df.columns:
                df = df[df['tokenAddress'] == token_mint_address]
            else:
                print(f"No se encontró columna 'address' o 'tokenAddress'. Columnas disponibles: {df.columns}")
                return pd.DataFrame()
            
            if not df.empty:
                # Renombra las columnas para mantener la consistencia con el formato anterior
                df = df.rename(columns={
                    'address': 'Mint Address',
                    'uiAmount': 'Amount',
                    'valueUsd': 'USD Value'
                })
                
                # Selecciona solo las columnas necesarias
                df = df[['Mint Address', 'Amount', 'USD Value']]
                
                print(f'Data found for {token_mint_address[:4]}:')
                print(df)
                return df
            else:
                print(f'No data found for token {token_mint_address[:4]}')
                return pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])
        else:
            print("No data available in the response.")
            return pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])
    
    except requests.RequestException as e:
        print(f"Error fetching data for token {token_mint_address[:4]}: {e}")
        return pd.DataFrame(columns=['Mint Address', 'Amount', 'USD Value'])

def pnl_close(token_mint_address):
    print(f'Checking PNL close for {token_mint_address[:4]}')
    balance = get_position(token_mint_address)
    print(f'Balance for {token_mint_address[:4]}: {balance}')

    price = token_price(token_mint_address)
    print(f'Price for {token_mint_address[:4]}: {price}')

    try:
        usd_value = float(balance) * float(price)
        print(f'USD value for {token_mint_address[:4]}: {usd_value}')
    except:
        usd_value = 0
        print(f'Error calculating USD value for {token_mint_address[:4]}')

    tp = ((1+TP) * USDC_SIZE)
    sl = ((1-SL) * USDC_SIZE)
    sell_size = balance * SELL_AMOUNT_PERC
    decimals = get_decimals(token_mint_address)
    sell_size = int(sell_size * 10 **decimals)
    
    print(f'For {token_mint_address[:4]}: USD value is {usd_value}, TP is {tp}, SL is {sl}')

    while usd_value > tp:
        with open(CLOSED_POSITIONS_TXT, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            if token_mint_address not in lines:
                with open(CLOSED_POSITIONS_TXT, 'a') as f:
                    f.write(token_mint_address + '\n')

        cprint(f'for {token_mint_address[:4]} value is {usd_value} and tp is {tp} so closing...', 'white', 'on_green')
        try:
            for _ in range(3):
                market_sell(token_mint_address, sell_size)
                cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_green')
                time.sleep(1)
            time.sleep(15)
        except:
            cprint('order error.. trying again', 'white', 'on_red')

        balance = get_position(token_mint_address)
        price = token_price(token_mint_address)
        usd_value = balance * price
        tp = TP * USDC_SIZE
        sell_size = balance * SELL_AMOUNT_PERC
        sell_size = int(sell_size * 10 **decimals)
        print(f'USD Value is {usd_value} | TP is {tp} ')

    else:
        hi = 'hi'

    if usd_value != 0:
        while usd_value < sl and usd_value > 0:
            sell_size = balance 
            sell_size = int(sell_size * 10 **decimals)

            cprint(f'for {token_mint_address[:4]} value is {usd_value} and sl is {sl} so closing as a loss...', 'white', 'on_blue')
            print(token_mint_address)
            with open(CLOSED_POSITIONS_TXT, 'r') as f:
                lines = [line.strip() for line in f.readlines()]
                if token_mint_address not in lines:
                    with open(CLOSED_POSITIONS_TXT, 'a') as f:
                        f.write(token_mint_address + '\n')

            try:
                for _ in range(3):
                    market_sell(token_mint_address, sell_size)
                    cprint(f'just made an order {token_mint_address[:4]} selling {sell_size} ...', 'white', 'on_blue')
                    time.sleep(1)
                time.sleep(15)
            except:
                cprint('order error.. trying again', 'white', 'on_red')

            balance = get_position(token_mint_address)
            price = token_price(token_mint_address)
            usd_value = balance * price
            tp = TP * USDC_SIZE
            sl = ((1+SL) * USDC_SIZE)
            sell_size = balance 
            sell_size = int(sell_size * 10 **decimals)
            print(f'balance is {balance} and price is {price} and usd_value is {usd_value} and tp is {tp} and sell_size is {sell_size} decimals is {decimals}')

            if usd_value == 0:
                print(f'successfully closed {token_mint_address[:4]} usd_value is {usd_value} so breaking loop...')
                break

        else:
            print(f'for {token_mint_address[:4]} value is {usd_value} and tp is {tp} so not closing...')
            time.sleep(10)
    else:
        print(f'for {token_mint_address[:4]} value is {usd_value} and tp is {tp} so not closing...')
        time.sleep(10)

def get_position(token_mint_address):
    print(f'getting position for {token_mint_address[:4]}')
    dataframe = fetch_wallet_token_single(MY_ADDRESS, token_mint_address)

    if dataframe.empty:
        print(f"No se encontró posición para {token_mint_address}")
        return 0
    
    # Asumiendo que 'Amount' es la columna correcta (con A mayúscula)
    if 'Amount' in dataframe.columns:
        return float(dataframe['Amount'].values[0])
    else:
        print(f"No se encontró columna 'Amount'. Columnas disponibles: {dataframe.columns}")
        return 0


def open_position(token_mint_address):

    ''' this will loop unitl the position is full, it uses the get_token_balance til its full '''

    cprint(f'opening position for {token_mint_address}...', 'white', 'on_blue')

    balance = get_position(token_mint_address) # problematic 
    buying_df = pd.read_csv(READY_TO_BUY_CSV)
    
    # only grab the row with the token_mint_address in it and turn it into a json key/value pair
    token_info = buying_df[buying_df['contract_address'] == token_mint_address].to_dict(orient='records')[0]
    #print(token_info)
    token_size = USDC_SIZE # setting this to usdc size cause the the buying_df is in token amounts not usd
    # float token size and balance
    
    token_size = float(token_size) # usdc amount since orders are in usdc / changed in buying_df()

    price = ask_bid(token_mint_address)
    
    balance = price * balance # this converts the balance to usddc

    balance = float(balance)

    size_needed = token_size - balance

    print(f'****** token size {token_size} price is {price} and balance is {balance} and size is {token_size}')

    with open(CLOSED_POSITIONS_TXT, 'r') as f:
        closed_positions = [line.strip() for line in f.readlines()]
    # closed_positions.txt acts as our black list

    # Check if the token mint address is not in the stripped lines of data/closed_positions.txt
    if token_mint_address not in closed_positions:

        while balance < (.9 * token_size):

            print(f'**Filling Position for {token_mint_address[:4]} : balance is {balance} and size is {token_size} size needed: {size_needed}')


            # FIGURE OUT THE DECIMALS FOR THE SELL OR WE MAY SELL A 9 DIGIT AT 6 DIGIT and RUN OUT OF SOL
            try:
                size_needed = int(size_needed * 10**6)
                size_needed = str(size_needed)
                print(f'buying this amount {size_needed} for {token_mint_address}')

                for i in range(ORDERS_PER_OPEN):
                    order = market_buy(token_mint_address, size_needed)
                    cprint(f'just made an order {token_mint_address[:4]} of size: {size_needed}', 'white', 'on_blue')

                    time.sleep(5)
            except:

                try:
                    cprint(f'trying again to make the order in 30 seconds.....', 'light_blue', 'on_light_magenta')

                    time.sleep(30)
                    print(f'buying this amount {size_needed} for {token_mint_address}')

                    for i in range(ORDERS_PER_OPEN):
                        order = market_buy(token_mint_address, size_needed)
                        cprint(f'just made an order {token_mint_address[:4]} of size: {size_needed}', 'white', 'on_blue')
                        time.sleep(5)

                except:
                    cprint('error in buy ---- the next print saying filled isnt true but good cuz logged to closed_positions.txt to not trade again.', 'white', 'on_red')
                    time.sleep(3)
                # current bug - if the order fails, it will never attempt to get back in. need to thnk of a way to handle this and not logged to closed_positions here 
                    break 
            # added this break here and now it assumes filliwe filled n puts on closed_positions.txt so we dont trade again
                

            price = ask_bid(token_mint_address)
            time.sleep(1)
            token_size = float(token_size)
            balance = get_position(token_mint_address)
            balance = float(balance)
            balance = price * balance # this converts the balance to usddc
            size_needed = token_size - balance
            print(f'22****** token size {token_size} price is {price} and balance is {balance} and size is {token_size} ')
    else:
        print('we have already opened OR closed that poistion so not opening again...')
        time.sleep(5)

    print(f'fully filled our position... ')

    with open(CLOSED_POSITIONS_TXT, 'a') as file:  # 'a' mode for appending to the file
        file.write(f'{token_mint_address}\n')  #

    price = ask_bid(token_mint_address)
    
    open_positions = fetch_wallet_holdings_og(MY_ADDRESS)

    # Check if 'open_price' column exists, if not create it with NaN values
    if 'open_price' not in open_positions.columns:
        open_positions['open_price'] = float('nan')

    # Update 'open_price' only if it's NaN for the specified 'token_mint_address'
    condition = (open_positions['Mint Address'] == token_mint_address) & open_positions['open_price'].isnull()
    open_positions.loc[condition, 'open_price'] = price

    open_positions.to_csv(TOKEN_PER_ADDY_CSV, index=False)
