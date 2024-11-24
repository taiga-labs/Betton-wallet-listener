import asyncio
import requests

from getters import *
from pytonapi import AsyncTonapi
from pytonapi.schema.events import TransactionEventData

async def send_response(response: NewTransferResponse):

    try:
        response = requests.post("https://xoma.monster/test/dep.php", data = response)

        if response.status_code == 200:
            print(response.text)
        else:
            print(f"Ошибка при отправке. Код ответа: {response.status_code}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


async def handle_message(event: TransactionEventData):
    
    transaction_hash = event.tx_hash
    transaction_info = await get_transaction_info(tx_hash=transaction_hash)
    source_address = await get_source_address(transaction_info)
    jetton_wallet_flag = await is_jetton_wallet(address=source_address)

    if jetton_wallet_flag:
        transfer_type = "JETTON"
        jetton_master = await get_jetton_master(jetton_wallet_address = source_address)
        jetton_symbol = await get_jetton_symbol(jetton_master = jetton_master)
        jetton_decimals = await get_jetton_decimals(jetton_master = jetton_master)
        amount = await get_transfer_amount(transaction_info, jetton_type = "JETTON", decimals = jetton_decimals)

    else:
        transfer_type = "TON"
        jetton_symbol = None
        jetton_master = None
        amount = await get_transfer_amount(transaction_info, jetton_type = "TON", decimals = 9)

    payload = await get_transfer_payload(transaction_info)

    response = NewTransferResponse(
        type=transfer_type,
        symbol=jetton_symbol or "null",
        sender=source_address,
        amount=amount,
        payload_text=payload,
        jetton_master_address=jetton_master,
        hash=transaction_hash,
    )

    await send_response(response = response)


async def main():

    tonapi = AsyncTonapi(api_key=os.getenv("TON_API_KEY"))
    accounts = ["UQA5o0JmVFBAnlXdS7kiMTZwLEvVHRaCoqWgrTSZDvc6EEU0"]

    await tonapi.websocket.subscribe_to_transactions(accounts=accounts, handler=handle_message)

    try:
        while True:
            await asyncio.sleep(1)
    except:
        await main()

if __name__ == '__main__':
    asyncio.run(main())