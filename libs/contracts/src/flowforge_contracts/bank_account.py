from pydantic import BaseModel


class BankAccountRef(BaseModel):
    last4: str
    fingerprint: str
    account_number: str
