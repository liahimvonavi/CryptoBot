import random
import requests
import json
import re
from time import sleep
from datetime import datetime
from Coin_manager_jupiter import JupiterSwap
from url_headers import involio_url, involio_headers, involio_payload, refresh_url, refresh_headers
from database import get_all_transactions
from constants import BUY_VALUE, MAIN_MINT, send_email




class InvolioScraper:
    def __init__(self):
        self.posts = {}
        self.last_post_id = None
        self.timestamp = datetime.now()
        self.processed_addresses = self.load_purchased_addresses()
        print(f"{self.timestamp} - Initializing Crawling...")
        print("-" * 100)
        print()

    def load_purchased_addresses(self):
        return {tx.wallet_address for tx in get_all_transactions()}

    def get_recent_posts(self):
        updated_headers = None
        while True:
            try:
                response = requests.request("POST", involio_url, headers=involio_headers if not updated_headers else involio_headers, data=involio_payload)
                response = json.loads(response.text)
                if "detail" in response.keys():
                    updated_headers = self.renew_headers()
                    continue
                for item in response["items"]:
                    post_id = item["id"]
                    content = item["content"]
                    created_at = item["createdAt"].replace("T", " ")
                    if post_id not in self.posts.keys():
                        print(created_at)
                        self.timestamp = datetime.now()
                        print(f"New post has been made: {content}")
                        print("*" * 100)
                        print()
                    self.posts[post_id] = content
                    self.last_post_id = post_id
                coin_address = self.extract_coin_address()


                if coin_address != "No address to be found." and coin_address not in self.processed_addresses:
                    print(f"Processing: {coin_address}...")
                    buyer = JupiterSwap()
                    buy_amount = int(BUY_VALUE * 10**9)
                    valid = buyer.jupiter_swap_transaction(input_mint=MAIN_MINT, output_mint=coin_address, amount=buy_amount)
                    if valid:
                        self.processed_addresses.add(coin_address)
            except Exception as e:
                msg = (
                    f"Subject: Failed checking\n\n"
                    f"The cause for it is Error: {e}"
                )
                send_email(msg)

            sleep(random.randint(5, 10))

    def renew_headers(self):
        response = requests.request("GET", refresh_url, headers=refresh_headers)
        new_token = json.loads(response.text)["refreshToken"]
        involio_headers["authorization"] = f"Bearer {new_token}"
        return involio_headers

    def extract_coin_address(self):
        pattern = r"\b[A-Za-z0-9]{30,}\b"
        matches = re.search(pattern, self.posts[self.last_post_id])
        return matches.group(0) if matches else "No address to be found."







data_scraper = InvolioScraper()
data_scraper.get_recent_posts()

