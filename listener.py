import asyncio
import aiohttp
import logging
from getters import *
from schemas import *
from pytoniq import Address
from pytonapi import AsyncTonapi
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


async def send_response(response: NewTransferResponse):

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://xoma.monster/test/dep.php",
                json = response
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logging.error(f"Failed to send response: {resp.status}, {text}")
    except Exception as e:
        logging.error(f"Error while sending response: {e}")


async def handle_message(event: TransactionEventData = None):

    try:
        transaction_hash = event.tx_hash
        transaction_info = get_transaction_info(tx_hash = transaction_hash)

        if isinstance(transaction_hash, AbstractErrorMessage):
            transaction_info = get_transaction_info(tx_hash = transaction_hash)

        source_address = get_source_address(transaction_info)

        logging.info(f"Source address: {source_address}")

        if source_address != ADMIN_WALLET_ADDRESS:

            jetton_wallet_flag = is_jetton_wallet(address = source_address)

            if jetton_wallet_flag:

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

            else:
                transfer_type = "TON"
                jetton_symbol = None
                jetton_master = None
                amount = get_transfer_amount(transaction_info, jetton_type = transfer_type, decimals = 9)

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

            await send_response(response = {
                "type": response.type,
                "symbol": response.symbol,
                "sender": response.sender,
                "amount": response.amount,
                "payload_text": response.payload_text,
                "jetton_master_address": response.hash
                }
            )
    except Exception as e:
        logging.error(f"Error handling message: {e}")


async def main():

    while True:
        try:
            tonapi = AsyncTonapi(api_key = TON_API_KEY)
            accounts = ["UQB4M_AbtopojI-EqoN9dfNZsSfFLcHZmYJQXP2_BIlazvxr"]

            await tonapi.websocket.subscribe_to_transactions(accounts = accounts, handler = handle_message)

            while True:
                await asyncio.sleep(1)

        except Exception as ex:
            logging.error(f"An error occurred: {ex}")
            logging.info("Restarting the program in 5 seconds...")
            await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())
