import typing

from http import HTTPStatus
from pydantic import BaseModel


class AbstractErrorMessage(BaseModel):
    message: str
    status_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR


class NewTransferResponse(BaseModel):
    type: str
    symbol: str
    sender: str
    amount: float
    payload_text: str
    jetton_master_address: typing.Optional[str]
    hash: str