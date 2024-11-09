import dontshare as d

# I CAN CHANGE THE AMOUNT OF TOKENS IN THE TRENDING_TOKENS IM BUYING BY TWEAKING THE BELOW.

# Configuration
USDC_SIZE = 1
MINUTES_TO_CHECK = 30  # Variable to set the time window for checking transactions
SLEEP_TIME = .1  # Time to sleep between checking each wallet
DAYS_BACK = 0 # how many days back to check for txs
TP = 29 # 30x return
SL = .6 # 60% loss
MAX_POSITIONS = 50
MIN_TRADES_LAST_HOUR  = 60
MAX_MARKET_CAP = 1000000
MIN_LIQUIDITY = 1000
UNIQUE_WALLETS = 30
MAX_DD = -70 # 70% drop
TOP_10PERC_MAX = .7 # IF MORE THAN 70% OF TOP 10 HOLDERS DROP, GET GHOSTED
DO_NOT_TRADE_LIST = ['So11111111111111111111111111111111111111111', 'Eq1qrNGCiCtcZhFUGDYAmRJQ2w9kdLPak1Gx4mvkTQCE', 'Q1BaFmfN8TXdMVS98RYMhFZWRzVTCp8tUDhqM9CgcAL','HiZZAjSHf8W53QPtWYzj1y9wqhdirg124fiEHFGiUpQh', 'AuabGXArmR3QwuKxT3jvSViVPscQASkFAvnGDQCE8tfm','rxkExwV2Gay2Bf1so4chsZj7f4MiLKTx45bd9hQy6dK','BmDXugmfBhqKE7S2KVdDnVSNGER5LXhZfPkRmsDfVuov','423scBCY2bzX6YyqwkjCfWN114JY3xvyNNZ1WsWytZbF','7S6i87ZY29bWNbkviR2hyEgRUdojjMzs1fqMSXoe3HHy', '8nBNfJsvtVmZXhbyLCBg3ndVW2Zwef7oHuCPjQVbRqfc','FqW3CJYF3TfR49WXRusxqCbJMNSjnay1A51sqP34ZxcB','EwsHNUuAtPc6SHkhMu8sQoyL6R4jnWYUU1ugstHXo5qQ','EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', '9Y9yqdNUL76v1ybpkQnVUj35traGEHXTBJB2b1iszFVv', 'Fd1hzhprThxCwz2tv5rTKyFeVCyEKRHaGqhT7hDh4fsW', '83227N9Fq4h1HMNnuKut61beYcB7fsCnRbzuFDCt2rRQ', 'J1oqg1WphZaiRDTfq7gAXho6K1xLoRMxVvVG5BBva3fh', 'GEvQuL9DT2UDtuTCCyjxm6KXEc7B5oguTHecPhKad8Dr'] 
SELL_AMOUNT_PERC = .7
ORDERS_PER_OPEN = 1
MIN_TRADES_30M_ONCE_IN_POSITION = 5

KEY = d.birdeye_api_key
TIMEFRAME_FOR_SMA = '4H'

RECENT_TXS_CSV = 'csvs/recenttxs.csv'
TRENDING_TOKENS_CSV = 'csvs/trending_tokens.csv'
PPL_TO_FOLLOW_CSV = 'csvs/ppl_to_follow.csv'
BOTS_TO_STUDY_CSV = 'csvs/bots_to_study.csv'
WALLET_TOKENS_CSV = 'csvs/wallet_tokens.csv'
CLOSED_POSITIONS_TXT = 'data/closed_positions.txt'
READY_TO_BUY_CSV = 'csvs/trending_tokens.csv'
TOKEN_PER_ADDY_CSV = 'csvs/token_per_addy.csv'

MY_ADDRESS = '4wgfCBf2WwLSRKLef9iW7JXZ2AfkxUxGM4XcKpHm3Sin'
USDC_CONTRACT_ADDRESS = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'