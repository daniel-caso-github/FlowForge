from dataclasses import dataclass
from decimal import Decimal


@dataclass
class SupplierProfile:
    tax_id: str
    detraction_rate: Decimal | None = None
    subject_to_irpf: bool = False
    irpf_rate: Decimal = Decimal("0.15")
