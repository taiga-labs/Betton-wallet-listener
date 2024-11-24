import os
import typing
import aiohttp

from schemas import *


async def get_transaction_info(tx_hash: str) -> typing.Union[dict, AbstractErrorMessage]:

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = f"{os.getenv("BASE_URL")}blockchain/transactions/{tx_hash}"
        async with session.get(url) as response:
            if response.status == 200:
                result = await response.json()
                return result or AbstractErrorMessage(message="Error: getTransactionInfo response is None")
            else:
                return AbstractErrorMessage(message=f"Error: Request failed with status: {response.status}")


async def get_source_address(transaction_info: dict) -> typing.Union[str, AbstractErrorMessage]:

    try:
        return transaction_info["in_msg"]["source"]["address"]
    except KeyError:
        return AbstractErrorMessage(message="Error: Unable to get source address")


async def is_jetton_wallet(address: str) -> typing.Union[bool, AbstractErrorMessage]:

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = f"{os.getenv("BASE_URL")}accounts/{address}"
        async with session.get(url) as response:
            if response.status == 200:
                result = await response.json()
                interfaces = result.get("interfaces", [])
                return "jetton_wallet" in interfaces
            else:
                return AbstractErrorMessage(message=f"Error: Request failed with status: {response.status}")


async def get_transfer_amount(transaction_info: dict, jetton_type: str, decimals: int = 9) -> typing.Union[float, AbstractErrorMessage]:

    try:
        if jetton_type == "TON":
            value = transaction_info["in_msg"]["value"]
            return float(value) / (10 ** decimals)
        elif jetton_type == "JETTON":
            decoded_body = transaction_info["in_msg"].get("decoded_body", {})
            amount = decoded_body.get("amount")
            return float(amount) / (10 ** decimals) if amount else 0.0
        else:
            return AbstractErrorMessage(message="Error: Unknown jetton type")
    except KeyError:
        return AbstractErrorMessage(message="Error: Unable to get transfer amount")


async def get_jetton_master(jetton_wallet_address: str) -> typing.Union[str, AbstractErrorMessage]:

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = f"{os.getenv("BASE_URL")}blockchain/accounts/{jetton_wallet_address}/methods/get_wallet_data"
        async with session.get(url) as response:
            if response.status == 200:
                result = await response.json()
                jetton_master = result.get("decoded", {}).get("jetton")
                return jetton_master or AbstractErrorMessage(message="Error: Jetton master is None")
            else:
                return AbstractErrorMessage(message=f"Error: Request failed with status: {response.status}")


async def get_jetton_symbol(jetton_master: str) -> typing.Union[str, AbstractErrorMessage]:

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = f"{os.getenv("BASE_URL")}jettons/{jetton_master}"
        async with session.get(url) as response:
            if response.status == 200:
                result = await response.json()
                jetton_symbol = result.get("metadata", {}).get("symbol")
                return jetton_symbol or AbstractErrorMessage(message="Error: Jetton symbol is None")
            else:
                return AbstractErrorMessage(message=f"Error: Request failed with status: {response.status}")


async def get_transfer_payload(transaction_info: dict) -> typing.Union[str, AbstractErrorMessage]:

    try:
        payload_text = transaction_info["in_msg"]["decoded_body"]["payload"]["message"]["message_internal"]["body"]["value"]["value"]["forward_payload"]["value"]["value"]["text"]
        return payload_text or ""
    except KeyError:
        return AbstractErrorMessage(message="Error: Unable to get transfer payload")


async def get_jetton_decimals(jetton_master: str) -> typing.Union[int, AbstractErrorMessage]:

    timeout = aiohttp.ClientTimeout(total = 30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        url = f"{os.getenv("BASE_URL")}jettons/{jetton_master}"
        async with session.get(url) as response:
            if response.status == 200:
                result = await response.json()
                jetton_decimals = int(result["metadata"]["decimals"])
                return jetton_decimals or AbstractErrorMessage(message="Error: Jetton symbol is None")
            else:
                return AbstractErrorMessage(message=f"Error: Request failed with status: {response.status}")