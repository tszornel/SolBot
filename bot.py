import schedule
import time
from CONFIG import *
import pandas as pd
from datetime import datetime
import watch_txs as w
import analyze_picks as a
import nice_funcs as n 
import time 
from termcolor import colored, cprint 

def bot():

    # RUN WATCH_TXS.PY TO GET THE LATEST TXS FROM COPY BOT
    w.run_main()

    print(f'DAYS_BACK: {DAYS_BACK}')
    print("Starting the bot...")
    df = pd.read_csv('csvs/recenttxs.csv')
    print(f"Length of df: {len(df)}")
    
    # Convertir la columna 'blockTime' a timestamp UTC
    df['blockTime'] = pd.to_datetime(df['blockTime'], utc=True)
    
    # Crear un timestamp UTC para hoy a las 00:00
    today_utc = pd.Timestamp.now(tz='UTC').replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Filtrar los datos
    if DAYS_BACK == 0:
        # Si DAYS_BACK es 0, mostrar solo los datos de hoy
        df = df[df['blockTime'] >= today_utc]
    else:
        # Si no, mostrar los datos de los últimos DAYS_BACK días
        df = df[df['blockTime'] > (today_utc - pd.Timedelta(days=DAYS_BACK))]
    
    print(f"Length of df after filter: {len(df)}")
    print(f"Date range in filtered df: {df['blockTime'].min()} to {df['blockTime'].max()}")
    
    # drop duplicates on the contract_address
    df = df.drop_duplicates(subset=['contract_address'])
    print(f"Length of df after removing duplicates: {len(df)}")

    # save to csv final_trending.csv and overwrite anything that exists
    df.to_csv('csvs/recenttxs.csv', index=False)

    # USE OUR ANALYZE_PICKS.PY TO ANALYZE THOSE TXS and save to trending_tokens
    a.analyze_picks() # outputs trending_tokens.csv

    # check wallet baalnace
    open_positions_df = n.fetch_wallet_holdings_og(MY_ADDRESS)

    print(f'open_positions_df: {open_positions_df}')

    # in df if mint_address = So11111111111111111111111111111111111111111 and Amount < .001 cprint red error, sleep for 5 minutes
    sol_df = open_positions_df[open_positions_df['Mint Address'] == 'So11111111111111111111111111111111111111111']

    # if sol_df is empty, sleep for 30 then try above again
    if sol_df.empty:
        cprint('😅 SOL BALANCE EMPTY... if happens lots, fix', 'white', 'on_magenta')
        time.sleep(30)
        open_positions_df = n.fetch_wallet_holdings_og(MY_ADDRESS)
        #print(open_positions_df)

        # in df if mint_address = So11111111111111111111111111111111111111111 and Amount < .001 cprint red error, sleep for 5 minutes
        sol_df = open_positions_df[open_positions_df['Mint Address'] == 'So11111111111111111111111111111111111111111']


    while sol_df['Amount'].values < .005:
        cprint('ERROR: SOL BALANCE IS LESS THAN .005', 'white', 'on_red')
        time.sleep(20)

        sol_df = n.fetch_wallet_token_single(MY_ADDRESS, 'So11111111111111111111111111111111111111111')

    # cprint sol balance in light blue bacckground white text 
    cprint(f'SOL BALANCE: {sol_df["Amount"].values}', 'white', 'on_light_blue')

    open_positions_count = open_positions_df.shape[0]
    winning_positions_df = open_positions_df[open_positions_df['USD Value'] > TP * USDC_SIZE]
    # print('this is the winning df')

    for index, row in winning_positions_df.iterrows():
        token_mint_address = row['Mint Address']

        # only pnl close if not usdc_contract_address
        cprint(f'Winning Loop - this is token mint address {token_mint_address} ', 'white', 'on_green')
        if token_mint_address not in DO_NOT_TRADE_LIST:
            #print(f'this is the token mint address {token_mint_address} ')
            
            n.pnl_close(token_mint_address)
        #print('done closing winning positions...')
        # same as above but cprint green
        cprint('done closing winning positions...', 'white', 'on_magenta')

    sl_size = ((1+SL) * USDC_SIZE)
    #print(f'now only keeping ones under the sl of {sl_size} we want to save time')
    losing_positions_df = open_positions_df[open_positions_df['USD Value'] < sl_size]
    #print('this is the losing df')
    
    # drop all rows that show 0 in USD Value
    losing_positions_df = losing_positions_df[losing_positions_df['USD Value'] != 0]

## NOW CHECKING LOSING POSITIONS - WE DO THIS 2nd TO CAPTURE PROFITS QUICKER
    for index, row in open_positions_df.iterrows():
        token_mint_address = row['Mint Address']

        # Check if the token mint address is in the DO_NOT_TRADE_LIST
        if token_mint_address in DO_NOT_TRADE_LIST:
            print(f'Skipping trading for {token_mint_address} as it is in the DO_NOT_TRADE_LIST')
            continue  # Skip to the next iteration

        # Note: This check might be redundant if 'usdc_contract_address' is already in DO_NOT_TRADE_LIST
        if token_mint_address != USDC_CONTRACT_ADDRESS:
            #print(f'This is the token mint address {token_mint_address}')
            n.pnl_close(token_mint_address)
    cprint('done closing losing positions.. keep swimming ❤️ 🙏.', 'white', 'on_magenta')

    # GRAB THE TRENDING TOKENS (READY TO BUY)
    df = pd.read_csv(TRENDING_TOKENS_CSV)
    print(f'trending_tokens_df: {df}')

    # look at closed_positions.txt and if the token is there, then remove that row from the df
    with open(CLOSED_POSITIONS_TXT, 'r') as f:
        closed_positions = [line.strip() for line in f.readlines()]

    # closed_positions.txt acts as our black list
    df = df[~df['contract_address'].isin(closed_positions)]
    # save df to ready_to_buy.csv
    df.to_csv(READY_TO_BUY_CSV, index=False)

    # 0. update the df to have the name in the first column
    df = pd.read_csv(READY_TO_BUY_CSV)
    df = n.get_names(df)

    if open_positions_count < MAX_POSITIONS:

        print(f'🚀 moondev.sol has {open_positions_count} open positions & max: {MAX_POSITIONS}')
        for index, row in df.iterrows():

            usdc_holdings = n.get_position(USDC_CONTRACT_ADDRESS)
            usdc_holdings = float(usdc_holdings)

            token_mint_address = row['contract_address']
            #print(f'this is the token mint address {token_mint_address} and this is the usdc address {usdc_contract_address}')
            
            if usdc_holdings > USDC_SIZE:

                print(f'we have {usdc_holdings} usdc so can open..')
                n.open_position(token_mint_address)
            else:
                cprint(f'we have {usdc_holdings} usdc holdings and we can not open a position', 'white', 'on_red')
            
            now = datetime.now()
            current_hour = now.hour
            current_minute = now.minute

            # break the loop if the condition is satisfied
            if current_hour % 2 == 0 and 9 <= current_minute <= 13:
                print('Breaking the loop to check the PnL')
                break
            
    else:
        print(f'we have {open_positions_count} open positions and we can not open more bc more than {MAX_POSITIONS}')


    # Sleep for a specified time before the next iteration
    time.sleep(5)  # Adjust the sleep time as needed

bot()
print('done with first run....')

if __name__ == "__main__":
    schedule.every(20).minutes.do(bot)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"Error in the scheduler: {str(e)}")
            time.sleep(60)