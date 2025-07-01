import os, json, requests, base58, base64, time
from dotenv import load_dotenv
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.types import TxOpts
from solders.transaction import VersionedTransaction
from solders.message import to_bytes_versioned
from database import add_transaction_to_db
from constants import send_email, MAIN_MINT, check_main_mint_price, BUY_VALUE, get_amount_from_tx
from decimal import Decimal, ROUND_DOWN
from datetime import datetime




class JupiterSwap:
    JUPITER_QUOTE_URL = "https://api.jup.ag/swap/v1/quote"
    JUPITER_SWAP_URL = "https://api.jup.ag/swap/v1/swap"

    def __init__(self):
        load_dotenv()
        PRIVATE_KEY = os.getenv("private_key")
        self.my_wallet = Keypair.from_bytes(base58.b58decode(PRIVATE_KEY))
        self.solana_client = Client("https://api.mainnet-beta.solana.com")

    def check_decimals_of_SPL(self, output_mint):
        mint_addr = Pubkey.from_string(output_mint)
        token_info = self.solana_client.get_token_supply(mint_addr)
        decimals = token_info.value.decimals
        return decimals

    def get_quote(self, input_mint, output_mint, amount):
        headers = {
            'Accept': 'application/json'
        }
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": "500",
            "swapMode": "ExactIn"
        }
        response = requests.request("GET", self.JUPITER_QUOTE_URL, params=params, headers=headers)
        return response.json()


    def jupiter_swap_transaction(self, input_mint, output_mint, amount):
        quote_response = self.get_quote(input_mint, output_mint, amount)
        if "error" in quote_response:
            print(f"Error fetching quote: {quote_response}")
            return False

        payload = json.dumps({
            "userPublicKey": str(self.my_wallet.pubkey()),
            "wrapAndUnwrapSol": True,
            "useSharedAccounts": False,
            "dynamicSlippage": True,
            "asLegacyTransaction": False,
            "quoteResponse": quote_response
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        swap_response = requests.request("POST", self.JUPITER_SWAP_URL, headers=headers, data=payload).json()

        if "swapTransaction" in swap_response:
            try:
                # Decode the serialized transaction received from Jupiter
                swap_tx_bytes = base64.b64decode(swap_response['swapTransaction'])

                # Deserialize into a VersionedTransaction
                versioned_tx = VersionedTransaction.from_bytes(swap_tx_bytes)

                # Sign the transaction's message bytes with your wallet's keypair
                signature = self.my_wallet.sign_message(to_bytes_versioned(versioned_tx.message))

                # Populate the transaction with the signature correctly
                signed_tx = VersionedTransaction.populate(
                    message=versioned_tx.message,
                    signatures=[signature]
                )

                # Serialize and submit the signed transaction correctly
                tx_opts = TxOpts(skip_preflight=True, preflight_commitment="confirmed", max_retries=5)
                transaction_confirmed = False
                try:
                    tx_result = self.solana_client.send_raw_transaction(bytes(signed_tx), opts=tx_opts)
                    tx_signature = tx_result.value
                    print(f"Transaction Signature: {tx_signature}")
                    print("Waiting confirmation.....")
                    time.sleep(3)

                    for i in range(5):
                        tx_status = self.solana_client.get_signature_statuses([tx_signature])
                        status = tx_status.value[0]
                        if status is not None:
                            if status.err is None:
                                print("Valid Transaction ✅")
                                transaction_confirmed = True
                                break
                            else:
                                print(f"Transaction failed X\n"
                                      f"Error: {status.err}")
                                msg= (
                                    f"Subject: Transaction failed X\n"
                                    f"Error: {status.err}"
                                )
                                send_email(msg)
                                return False
                            time.sleep(3)

                        else:
                            print("Transaction status not found, retrying...")
                            time.sleep(3)

                    if transaction_confirmed:
                        if input_mint == MAIN_MINT:
                            sol_price = check_main_mint_price()
                            time.sleep(10)
                            total_tokens = get_amount_from_tx(str(tx_signature))
                            price_per_token = Decimal(BUY_VALUE * sol_price / total_tokens).quantize(Decimal('0.0000000001'), rounding = ROUND_DOWN)
                            invested_amount = (sol_price * BUY_VALUE).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
                            add_transaction_to_db(wallet_address=output_mint, amount_of_coins=total_tokens, invested_amount = invested_amount,
                                                  price=price_per_token)

                            msg = (
                                f"Subject: Bought a coin\n\n"
                                f"You have bought successfully {total_tokens} coins at a current price of {price_per_token}.\n\n "
                                f"This is the address of the coin: {output_mint}\n\n"
                                f"Hope you get a clean 1.5x on that  {amount / 10 ** 9}Sol you invested.")
                            send_email(msg)
                            return True
                        return True


                    print("⚠️ Warning: Transaction may be stuck in pending state.")

                except Exception as e:
                    print(f"Transaction failed retrying... Error: {e}")
                    msg=(
                        f"Subject: Failed transaction\n\n"
                        f"The cause for it is Error: {e}"
                    )
                    send_email(msg)



            except Exception as e:
                print(f"Transaction signing/sending error: {e}")
                return False
        else:
            print(f"Swap Error: {swap_response}")
            msg = (f"Subject: Error\n\n"
                   f"Didn't get that swap cause of {swap_response}")
            send_email(msg)
            return False


