import asyncio
import aiohttp
import requests

from getters import *
from schemas import *
from pytoniq import Address
from pytonapi import AsyncTonapi
from pytonapi.schema.events import TransactionEventData
from pytonapi.exceptions import TONAPIError

ADMIN_WALLET_ADDRESS = ""
ADMIN_JETTON_WALLET_ADDRESS = ""


async def send_response(response: NewTransferResponse):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://xoma.monster/test/dep.php",
                json=response
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"Failed to send response: {resp.status}, {text}")
    except Exception as e:
        print(f"Error while sending response: {e}")


async def handle_message(event: TransactionEventData = None):
    
    # transaction_hash = event.tx_hash
    transaction_hash = "d268d13a2708652095b4a9fe4f3d6433b290e52d1528d18c8a2e32eaced7cc1c"
    transaction_info = get_transaction_info(tx_hash=transaction_hash)

    print(transaction_info)

    if isinstance(transaction_hash, AbstractErrorMessage): transaction_info = get_transaction_info(tx_hash = transaction_hash)

    source_address = get_source_address(transaction_info)

    print(source_address)

    if source_address != ADMIN_WALLET_ADDRESS or source_address != ADMIN_JETTON_WALLET_ADDRESS: 

        jetton_wallet_flag = is_jetton_wallet(address=source_address)

        if jetton_wallet_flag:
            transfer_type = "JETTON"
            jetton_master = get_jetton_master(jetton_wallet_address = source_address)
            jetton_symbol = get_jetton_symbol(jetton_master = jetton_master)
            jetton_decimals = get_jetton_decimals(jetton_master = jetton_master)
            amount = get_transfer_amount(transaction_info, jetton_type = transfer_type, decimals = jetton_decimals)

        else:
            transfer_type = "TON"
            jetton_symbol = None
            jetton_master = None
            amount = get_transfer_amount(transaction_info, jetton_type =  transfer_type, decimals = 9)

        payload = get_transfer_payload(transaction_info, jetton_type = transfer_type)

        response = NewTransferResponse(
            type=transfer_type,
            symbol=jetton_symbol or "null",
            sender=source_address,
            amount=amount,
            payload_text=payload,
            jetton_master_address=jetton_master,
            hash=transaction_hash,
        )

        print(response)
        
        await send_response(response = {
            "type": response.type,
            "symbol": response.symbol,
            "sender": response.sender,
            "amount": response.amount,
            "payload_text": response.payload_text,
            "jetton_master_address": response.hash
            }
        )


async def main():
    while True:
        try:
            tonapi = AsyncTonapi(api_key=os.getenv("YOUR_API_KEY"))
            accounts = ["UQA5o0JmVFBAnlXdS7kiMTZwLEvVHRaCoqWgrTSZDvc6EEU0"]

            await tonapi.websocket.subscribe_to_transactions(accounts=accounts, handler=handle_message)
    
            while True: await asyncio.sleep(1)

        except Exception as ex:
            print(f"Произошла ошибка: {ex}")
            print("Перезапуск программы через 5 секунд...")

if __name__ == '__main__':
    asyncio.run(main())
