import random
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4

from flowforge_contracts.jurisdiction import Jurisdiction
from jurisdiction_packs.es.bank_account import generate_valid_iban
from jurisdiction_packs.es.tax_id import generate_valid_cif
from jurisdiction_packs.pe.bank_account import generate_valid_cci
from jurisdiction_packs.pe.tax_id import generate_valid_ruc
from jurisdiction_packs.profiles import SupplierProfile


@dataclass
class Company:
    id: UUID
    name: str
    tax_id: str
    jurisdiction: Jurisdiction


@dataclass
class Supplier:
    name: str
    tax_id: str
    jurisdiction: Jurisdiction
    bank_account_kind: str
    bank_account_number: str
    profile: SupplierProfile


@dataclass
class Product:
    description: str
    unit_price: Decimal
    currency: str


@dataclass
class MasterDataWorld:
    companies: list[Company]
    suppliers: list[Supplier]
    products: list[Product]


def _random_digits(rng: random.Random, count: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(count))


def _pe_company(rng: random.Random, name: str) -> Company:
    return Company(id=uuid4(), name=name, tax_id=generate_valid_ruc(_random_digits(rng, 10)), jurisdiction="PE")


def _es_company(rng: random.Random, name: str) -> Company:
    return Company(
        id=uuid4(), name=name, tax_id=generate_valid_cif("B", _random_digits(rng, 7)), jurisdiction="ES"
    )


def _pe_supplier(rng: random.Random, name: str, with_detraction: bool) -> Supplier:
    ruc = generate_valid_ruc(_random_digits(rng, 10))
    profile = SupplierProfile(tax_id=ruc, detraction_rate=Decimal("0.12") if with_detraction else None)
    return Supplier(
        name=name, tax_id=ruc, jurisdiction="PE", bank_account_kind="CCI",
        bank_account_number=generate_valid_cci(_random_digits(rng, 18)), profile=profile,
    )


def _es_supplier(rng: random.Random, name: str, with_irpf: bool) -> Supplier:
    cif = generate_valid_cif("B", _random_digits(rng, 7))
    profile = SupplierProfile(tax_id=cif, subject_to_irpf=with_irpf, irpf_rate=Decimal("0.15"))
    return Supplier(
        name=name, tax_id=cif, jurisdiction="ES", bank_account_kind="IBAN",
        bank_account_number=generate_valid_iban(_random_digits(rng, 20)), profile=profile,
    )


PE_PRODUCTS = [
    ("Consultoria de software", Decimal("150.00")),
    ("Servicio de mantenimiento", Decimal("80.00")),
    ("Licencia de uso anual", Decimal("500.00")),
]
ES_PRODUCTS = [
    ("Consultoria informatica", Decimal("180.00")),
    ("Servicio de soporte", Decimal("90.00")),
    ("Licencia anual", Decimal("550.00")),
]


def generate_master_data(seed: int) -> MasterDataWorld:
    rng = random.Random(seed)
    companies = [_pe_company(rng, "Andina Retail S.A.C."), _es_company(rng, "Iberia Retail S.L.")]
    suppliers = [
        _pe_supplier(rng, "Consultora Lima SAC", with_detraction=True),
        _pe_supplier(rng, "Servicios Peru EIRL", with_detraction=False),
        _es_supplier(rng, "Consultoria Madrid SL", with_irpf=True),
        _es_supplier(rng, "Servicios Barcelona SL", with_irpf=False),
    ]
    products = [
        Product(description=desc, unit_price=price, currency="PEN") for desc, price in PE_PRODUCTS
    ] + [
        Product(description=desc, unit_price=price, currency="EUR") for desc, price in ES_PRODUCTS
    ]
    return MasterDataWorld(companies=companies, suppliers=suppliers, products=products)
