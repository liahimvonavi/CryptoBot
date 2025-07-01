import smtplib, os, time, json
from dotenv import load_dotenv
import requests
from decimal import Decimal, ROUND_DOWN
from url_headers import jupiter_price_url


load_dotenv()

WSOL_MINT = "So11111111111111111111111111111111111111112"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"


BUY_VALUE = Decimal(0.01) # ----------> Amount of Sol you want to invest! <----------------#
MAIN_MINT = WSOL_MINT # ----------> Mint address you want to trade with <----------------#



from decimal import Decimal, ROUND_DOWN
import requests
import json
import time

WSOL_MINT = "So11111111111111111111111111111111111111112"  # Replace with actual WSOL mint if different

def get_amount_from_tx(signature: str) -> Decimal | None:
    time.sleep(10)
    url = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [
            signature,
            {"encoding": "json", "maxSupportedTransactionVersion": 0}
        ]
    }

    while True:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()

        if result.get("result") is None:
            print(f"⏳ Transaction not ready, retrying...")
            time.sleep(1.5)
            continue

        meta = result["result"]["meta"]
        post_tokens = meta.get("postTokenBalances", [])
        pre_tokens = meta.get("preTokenBalances", [])

        # Index preTokenBalances by accountIndex for reliable matching
        pre_map = {entry["accountIndex"]: entry for entry in pre_tokens}

        for post in post_tokens:
            mint = post["mint"]
            if mint == WSOL_MINT:
                continue  # Skip WSOL

            decimals = int(post["uiTokenAmount"]["decimals"])
            post_amt = Decimal(post["uiTokenAmount"]["amount"])
            account_index = post["accountIndex"]

            pre_amt = Decimal(0)
            if account_index in pre_map:
                pre_amt = Decimal(pre_map[account_index]["uiTokenAmount"]["amount"])

            delta = post_amt - pre_amt
            if delta > 0:
                received = (delta / Decimal(10 ** decimals)).quantize(Decimal("0.00001"), rounding=ROUND_DOWN)
                print(f"✅ Token Mint: {mint}")
                print(f"💰 Received: {received}")
                return received

        print("⚠️ No positive token delta found.")
        return None



def check_main_mint_price():
    try:
        response = requests.get(jupiter_price_url, params={"ids": MAIN_MINT}, timeout=10)
        data = response.json()
        price_sol = Decimal(data["data"][MAIN_MINT]["price"]).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
        return price_sol
    except requests.exceptions.RequestException as e:
        print(f" Failed to fetch SOL price: {e}")



def send_email(msg):
    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(user=os.getenv("EMAIL"), password=os.getenv("token_gmail"))
        connection.sendmail(from_addr=os.getenv("EMAIL"),
                            to_addrs=os.getenv("EMAIL"),
                            msg=msg)


