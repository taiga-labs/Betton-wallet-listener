import json
import asyncio
import aiohttp
import logging
from getters import *
from schemas import *
from pytoniq import Address
from pytonapi import AsyncTonapi
from urllib.parse import urlencode
from pytonapi.exceptions import TONAPIError
from pytonapi.schema.events import TransactionEventData


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)


TON_API_KEY = "3751b902af2e0fccb69c5c279e23e0ed8dadadcc10a441e3fc3b43172595f4ea"
ADMIN_WALLET_ADDRESS = Address("UQB4M_AbtopojI-EqoN9dfNZsSfFLcHZmYJQXP2_BIlazvxr").to_str(is_user_friendly = False)


async def send_response(response: dict):

    header = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://xoma.monster/test/dep.php",
                data = response,
                headers = header
            ) as resp:
                logging.info(f"Sending response: {response}")
                if resp.status != 200:
                    text = await resp.text()
                    logging.error(f"Failed to send response: {resp.status}, {text}")
                logging.info(f"response: {response}")
    except Exception as e:
        logging.error(f"Error while sending response: {e}")


async def handle_message(event: TransactionEventData):
    
    try:
        transaction_hash = event.tx_hash
        transaction_info = get_transaction_info(tx_hash = transaction_hash)

        if isinstance(transaction_hash, AbstractErrorMessage):
            transaction_info = get_transaction_info(tx_hash = transaction_hash)

        source_address = get_source_address(transaction_info)

        logging.info(f"Source address: {source_address} | Admin wallet address {ADMIN_WALLET_ADDRESS}")

        if source_address != ADMIN_WALLET_ADDRESS:

            jetton_wallet_flag = is_jetton_wallet(address = source_address)

            if jetton_wallet_flag == "JETTON_WALLET":

                source_address = get_sender_jetton_wallet(transaction_hash = transaction_hash, source_address = source_address)
                jetton_wallet_owner = get_jetton_wallet_owner(jetton_wallet_address = source_address)

                if jetton_wallet_owner == ADMIN_WALLET_ADDRESS:
                    logging.info("Transfer from admin wallet")
                    return

                transfer_type = "JETTON"
                jetton_master = get_jetton_master(jetton_wallet_address = source_address)
                jetton_symbol = get_jetton_symbol(jetton_master = jetton_master)
                jetton_decimals = get_jetton_decimals(jetton_master = jetton_master)
                amount = get_transfer_amount(transaction_info, jetton_type = transfer_type, decimals = jetton_decimals)

            elif jetton_wallet_flag == "TON":
                transfer_type = "TON"
                jetton_symbol = None
                jetton_master = None
                amount = get_transfer_amount(transaction_info, jetton_type = transfer_type, decimals = 9)
            else: 
                logging.info("Recieved NFT")
                return

            payload = get_transfer_payload(transaction_info, jetton_type = transfer_type)

            response = NewTransferResponse(
                type = transfer_type,
                symbol = jetton_symbol or "null",
                sender = source_address,
                amount = amount,
                payload_text = payload,
                jetton_master_address = jetton_master,
                hash = transaction_hash,
            )

            logging.info(f"Response: {response}")

            if transfer_type == "TON": jetton_master_address = "None"
            else: jetton_master_address = Address(response.jetton_master_address).to_str()

            await send_response(response = {
                "type": response.type,
                "symbol": response.symbol,
                "sender": Address(response.sender).to_str(),
                "amount": response.amount,
                "payload_text": response.payload_text,
                "jetton_master_address": jetton_master_address,
                "hash": response.hash
                }
            )
        else:
            logging.info("Transfer from admin wallet")
    except Exception as e:
        logging.error(f"Error handling message: {e}")


async def main():

    while True:
        try:
            tonapi = AsyncTonapi(api_key = TON_API_KEY)
            accounts = ["UQB4M_AbtopojI-EqoN9dfNZsSfFLcHZmYJQXP2_BIlazvxr"]
            logging.info("Start listening...")
            await tonapi.websocket.subscribe_to_transactions(accounts = accounts, handler = handle_message)
        except Exception as ex:
            logging.error(f"An error occurred: {ex}")
            logging.info("Restarting the program in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())
