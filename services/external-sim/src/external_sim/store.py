class InMemoryStore:
    def __init__(self) -> None:
        self._erp_invoices: dict[str, dict] = {}
        self._payments: dict[str, dict] = {}

    def post_invoice(self, idempotency_key: str, invoice_id: str, company_id: str) -> str:
        if idempotency_key not in self._erp_invoices:
            self._erp_invoices[idempotency_key] = {
                "invoice_id": invoice_id,
                "company_id": company_id,
                "status": "posted",
            }
        return self._erp_invoices[idempotency_key]["status"]

    def void_invoice(self, idempotency_key: str) -> str:
        record = self._erp_invoices.get(idempotency_key)
        if record is None:
            return "not_found"
        record["status"] = "voided"
        return record["status"]
