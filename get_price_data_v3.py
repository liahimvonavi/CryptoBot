import requests, time
from Coin_manager_jupiter import JupiterSwap
from url_headers import jupiter_price_url
from database import get_all_transactions, sold_coin
from decimal import Decimal, ROUND_DOWN
from constants import send_email, MAIN_MINT, check_main_mint_price
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
valid = False


while True:
    all_transactions = get_all_transactions()
    if not all_transactions:
        print("No transactions yet")
        time.sleep(10)

    else:

        for tx in all_transactions:
            if tx.already_sold:
                continue
            else:
                wallet = tx.wallet_address
                jupiter_price_params = {
                    "ids": wallet
                }
                response = requests.request("GET", jupiter_price_url, params=jupiter_price_params).json()
                price = Decimal(response["data"][wallet]["price"]).quantize(Decimal('0.0000000001'), rounding=ROUND_DOWN)

                bought_at_price = Decimal(tx.price).quantize(Decimal('0.0000000001'), rounding=ROUND_DOWN)
                total_coins = Decimal(tx.amount_of_coins).quantize(Decimal('0.0000000001'), rounding=ROUND_DOWN)


                print(datetime.now())
                print("-" * 50)
                print(f"Current price is: {price}")
                print(f"You bought at the price of: {bought_at_price}")
                print(f"Amount of coins you bought: {total_coins}")
                print("*" * 100)
                print()
                time.sleep(1)

                now = datetime.now()

                if price >= bought_at_price * Decimal(2):
                    seller = JupiterSwap()
                    decimals = seller.check_decimals_of_SPL(output_mint=wallet)
                    amount = int(tx.amount_of_coins * 10**decimals)
                    human_readable_amount = Decimal(amount / 10 ** decimals).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
                    result = (Decimal(human_readable_amount * price) - Decimal(tx.invested_amount)).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)

                    price_sol = check_main_mint_price()
                    valid = seller.jupiter_swap_transaction(input_mint=wallet, output_mint=MAIN_MINT, amount=amount)
                    if valid:
                        sold_coin(tx, result)

                        msg=(
                            f"Subject: Sold a coin successfully\n\n"
                            f"You have successfully sold {amount / 10**decimals} coins  at a current price of {price}.\n\n "
                            f"This is the address of the coin: {wallet}\n\n"
                            f"You deserved that boost of {Decimal(((human_readable_amount * price) - (human_readable_amount * bought_at_price)) / price_sol).quantize(Decimal('0.00001'))} Sol")
                        send_email(msg)

                if price <= bought_at_price * Decimal(0.5):
                    seller = JupiterSwap()
                    decimals = seller.check_decimals_of_SPL(output_mint=wallet)
                    amount = int(tx.amount_of_coins * 10 ** decimals)
                    human_readable_amount = Decimal(amount / 10 ** decimals).quantize(Decimal('0.00001'),
                                                                                   rounding=ROUND_DOWN)
                    result = (Decimal(human_readable_amount * price) - Decimal(tx.invested_amount)).quantize(
                     Decimal('0.00001'), rounding=ROUND_DOWN)

                    price_sol = check_main_mint_price()
                    valid = seller.jupiter_swap_transaction(input_mint=wallet, output_mint=MAIN_MINT, amount=amount)
                    if valid:
                        sold_coin(tx, result)

                        msg=(
                            f"Subject: Sold at a loss\n\n"
                            f"You sold {amount / 10**decimals} coins  at a current price of {price}.\n\n "
                            f"This is the address of the coin: {wallet}\n\n"
                            f"You got lost {Decimal(((human_readable_amount * price) - (human_readable_amount * bought_at_price)) / price_sol).quantize(Decimal('0.00001'))} Sol")
                        send_email(msg)





    time.sleep(2)

