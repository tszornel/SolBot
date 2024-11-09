<<<<<<< HEAD
# SOLANA COPY TRADER BOT - starting bal 631


# HOW TO USE
1. main.py
    - put a contract address into the main file, then run it to see all the early buyers of a token. you can configure the size
        - this outputs the trades over the size into the data folder
2. filter_data.py
    - this file removes duplicates and organizes the above data and puts it in a data/filtered folder which is better to work with 
3. by hand - i went through and opened up all the links on gmgn to decide which wallets i wanted to follow and put them on a txt file
    - i looked at win rate, pnl and diversity of wins
    - if there were a ton of trades per day, and if a lot that bought and sold the same token back to back, then i assumed it was a bot and labeled a bot
    - if there were not a lot of trades or quick buys then sells, i assumed it was a human trader
    - after writing all them down, i split them into two csvs one called pp_to_follow.csv and one called bots_to_study.csv
4. create_copy_csv.py
    - this file added a solscan link to the bots_to_study and ppl_to_follow csvs 
    - adds wallet_address
(paused for ic)
5. track_top_trader.py 
    - looks at each of the top traders in ppl_to_follow.py and outputs the total held for specific tokens across those top holders.. 
        - outputs to top_memes.txt which is a tracker of the top tokens across all those wallets
[ABOVE IS ALL RAN INDEPENDENTLY]


[BELOW IS ALL RUN IN THE BOT.py]
6. watch_txs.py
    - this one looks at the txs in the last X minutes of each of the wallets and then prints them out
    - now runs every 10 mins and outputs everything needed to buy or sell into a recenttxs.csv
7. analyze_picks.py 
    - this essentially sees which of the tokens are above the 4 20ma
    - max dd
    - low trade amounts
    - looking at ohlcv
    - this file essentially is where i get strict on dropping tokens.=
8. bot.py 
    - this combines the watc_txs and analyze picks to run every 10 mins so its always watching the ppl_to_follow.csv and then seeing their txs and then filtering to only ones > 4hr 20 sma
    - first rendition of this is going to be a hard stop loss and tp -- 10x return or 60% loss
    things to add
    - must have 40+ trades in last 1 hour
    - must be < X mcap (10m)
    - if VOL dries up on an open Position, aka less than 20 trades / hr, close position
    - if this is more than 70% off its high, get ghost
    - if mintable, drop
    - if top 10% holder > 50% drop
    - liquidity > 1000
    - drop usdc or solana EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
    - make sure there ar 30+ unique wallers
    - do a second, short term check, cause rn im looking at the ma of about 3 days.. 
        - update to have a short term ma of 20 15min periods which is about 5 hours.. 
            - think about this more, the end goal is really to get the trending tokens to actyall be trending
*nice_funcs.py
9. bot.py - is done
    - scans new tx's
    - filters those tokens
    - checks pnl_close
    - enters new positions

now, implement your strategy and be careful. this will all go to zero when solana stops trending.
=======
# SolBot
Sol bot 
>>>>>>> 9ce17b3b8ec0c4f2e790e63e17a9b404d91f3d49
