import os
import typing
import requests
import logging
from schemas import AbstractErrorMessage


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

BASE_URL = "https://tonapi.io/v2/"

def get_transaction_info(tx_hash: str) -> typing.Union[dict, AbstractErrorMessage]:

    url = f"{BASE_URL}blockchain/transactions/{tx_hash}"
    headers = {'Accept': 'application/json'}
    timeout = 30

    for attempt in range(3):  
        try:
            logging.info(f"Attempting to fetch transaction info (Attempt {attempt + 1}): {url}")
            response = requests.get(url, headers = headers, timeout = timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching transaction info: {e}")
            if attempt == 2:
                return AbstractErrorMessage(message = "Error: Unable to fetch transaction info")
            continue


def get_source_address(transaction_info: dict, jetton_type: str = None) -> typing.Union[str, AbstractErrorMessage]:

    try:
        try:
            return transaction_info["out_msgs"][0]['source']["address"]
        except:
            return transaction_info["in_msg"]["source"]["address"]
    except KeyError as e:
        logging.error(f"Key error: {e}")
        return AbstractErrorMessage(message = "Error: Unable to get source address")


def is_jetton_wallet(address: str) -> typing.Union[bool, AbstractErrorMessage]:

    url = f"{BASE_URL}accounts/{address}"
    headers = {'Accept': 'application/json'}
    timeout = 30

    for attempt in range(3):
        try:
            logging.info(f"Checking if address is a jetton wallet (Attempt {attempt + 1}): {url}")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            interfaces = result.get("interfaces", [])
            return "jetton_wallet" in interfaces
        except requests.exceptions.RequestException as e:
            logging.error(f"Error checking jetton wallet: {e}")
            if attempt == 2:
                return AbstractErrorMessage(message = "Error: Unable to determine if address is a jetton wallet")
            continue


def get_transfer_amount(transaction_info: dict, jetton_type: str, decimals: int = 9) -> typing.Union[float, AbstractErrorMessage]:

    try:
        if jetton_type == "TON":
            amount = transaction_info["out_msgs"][0]["value"]
            return float(amount / (10 ** decimals))
        elif jetton_type == "JETTON":
            decoded_body = transaction_info["in_msg"].get("decoded_body", {})
            amount = decoded_body.get("amount")
            return float(amount) / (10 ** decimals) if amount else 0.0
        else:
            return AbstractErrorMessage(message = "Error: Unknown jetton type")
    except KeyError as e:
        logging.error(f"Key error when accessing transfer amount: {e}")
        return AbstractErrorMessage(message = "Error: Unable to get transfer amount")


def get_jetton_master(jetton_wallet_address: str) -> typing.Union[str, AbstractErrorMessage]:

    url = f"{BASE_URL}blockchain/accounts/{jetton_wallet_address}/methods/get_wallet_data"
    headers = {'Accept': 'application/json'}
    timeout = 30

    for attempt in range(3):
        try:
            logging.info(f"Fetching jetton master (Attempt {attempt + 1}): {url}")
            response = requests.get(url, headers = headers, timeout = timeout)
            response.raise_for_status()
            result = response.json()
            jetton_master = result.get("decoded", {}).get("jetton")
            if jetton_master:
                return jetton_master
            else:
                return AbstractErrorMessage(message = "Error: Jetton master is None")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching jetton master: {e}")
            if attempt == 2:
                return AbstractErrorMessage(message = "Error: Unable to fetch jetton master")
            continue


def get_jetton_symbol(jetton_master: str) -> typing.Union[str, AbstractErrorMessage]:

    url = f"{BASE_URL}jettons/{jetton_master}"
    headers = {'Accept': 'application/json'}
    timeout = 30

    for attempt in range(3):
        try:
            logging.info(f"Fetching jetton symbol (Attempt {attempt + 1}): {url}")
            response = requests.get(url, headers = headers, timeout = timeout)
            response.raise_for_status()
            result = response.json()
            jetton_symbol = result.get("metadata", {}).get("symbol")
            if jetton_symbol:
                return jetton_symbol
            else:
                return AbstractErrorMessage(message = "Error: Jetton symbol is None")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching jetton symbol: {e}")
            if attempt == 2:
                return AbstractErrorMessage(message = "Error: Unable to fetch jetton symbol")
            continue


def get_transfer_payload(transaction_info: dict, jetton_type: str) -> typing.Union[str, AbstractErrorMessage]:

    try:
        if jetton_type != "TON":
            payload_text = transaction_info["in_msg"]["decoded_body"]["forward_payload"]["value"]["value"]["text"]
        else:
            payload_text = transaction_info["out_msgs"][0]["decoded_body"]["text"]

        return str(payload_text) or ""
    except KeyError as e:
        logging.error(f"Key error when accessing transfer payload: {e}")
        return AbstractErrorMessage(message = "Error: Unable to get transfer payload")


def get_jetton_decimals(jetton_master: str) -> typing.Union[int, AbstractErrorMessage]:

    url = f"{BASE_URL}jettons/{jetton_master}"
    headers = {'Accept': 'application/json'}
    timeout = 30

    for attempt in range(3):
        try:
            logging.info(f"Fetching jetton decimals (Attempt {attempt + 1}): {url}")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            jetton_decimals = int(result["metadata"]["decimals"])
            return jetton_decimals
        except (KeyError, ValueError) as e:
            logging.error(f"Error parsing jetton decimals: {e}")
            return AbstractErrorMessage(message = "Error: Jetton decimals not found")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching jetton decimals: {e}")
            if attempt == 2:
                return AbstractErrorMessage(message = "Error: Unable to fetch jetton decimals")
            continue


def get_jetton_wallet_owner(jetton_wallet_address: str) -> typing.Union[str, AbstractErrorMessage]:

    url = f"{BASE_URL}blockchain/accounts/{jetton_wallet_address}/methods/get_wallet_data"
    headers = {'Accept': 'application/json'}
    timeout = 30

    for attempt in range(3):
        try:
            logging.info(f"Fetching jetton master (Attempt {attempt + 1}): {url}")
            response = requests.get(url, headers = headers, timeout = timeout)
            response.raise_for_status()
            result = response.json()
            owner_address = result.get("decoded", {}).get("owner")
            if owner_address:
                return owner_address
            else:
                return AbstractErrorMessage(message = "Error: Owner address is None")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching owner address: {e}")
            if attempt == 2:
                return AbstractErrorMessage(message = "Error: Unable to fetch owner address")
            continue

def get_sender_jetton_wallet(transaction_hash: str, source_address: str) -> typing.Union[str, AbstractErrorMessage]:
    
    url = f"{BASE_URL}accounts/{source_address}/events/{transaction_hash}"
    headers = {'Accept': 'application/json'}
    timeout = 30

    for attempt in range(3):
        try:
            logging.info(f"Fetching jetton master (Attempt {attempt + 1}): {url}")
            response = requests.get(url, headers = headers, timeout = timeout)
            response.raise_for_status()
            result = response.json()
            sender_address = result["actions"][0]["JettonTransfer"]["senders_wallet"]

            if sender_address:
                return sender_address
            else:
                return AbstractErrorMessage(message = "Error: Owner address is None")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching owner address: {e}")
            if attempt == 2:
                return AbstractErrorMessage(message = "Error: Unable to fetch owner address")
            continue