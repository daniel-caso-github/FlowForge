import hashlib
import json
import random
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from flowforge_contracts.canonical_invoice import CanonicalCreditNote, CanonicalInvoice
from jurisdiction_packs.es.pack import SpainJurisdictionPack
from jurisdiction_packs.pe.pack import PeruJurisdictionPack

from datagen.degradation import degrade
from datagen.ground_truth import build_invoice
from datagen.master_data import MasterDataWorld, generate_master_data
from datagen.scenarios import (
    build_credit_note,
    build_duplicate_pair,
    inject_invalid_tax_id,
    inject_missing_withholding,
    inject_multi_currency,
    inject_wrong_tax_calculation,
)

SCENARIO_COUNTS = {
    "dev": {
        "happy_path": 75, "happy_path_with_withholding": 45, "wrong_tax_calculation": 15,
        "missing_withholding": 15, "invalid_tax_id": 15, "multi_currency": 15,
        "credit_note_full": 15, "credit_note_partial": 15, "duplicate_pair": 15, "multi_line": 15,
    },
    "test": {
        "happy_path": 23, "happy_path_with_withholding": 13, "wrong_tax_calculation": 3,
        "missing_withholding": 3, "invalid_tax_id": 3, "multi_currency": 3,
        "credit_note_full": 3, "credit_note_partial": 3, "duplicate_pair": 3, "multi_line": 3,
    },
}


@dataclass
class DatasetRecord:
    record_id: str
    split: str
    jurisdiction: str
    scenario: str
    invoice_json_path: str | None
    xml_path: str | None
    credit_note_json_path: str | None


def _pack_for(jurisdiction: str):
    return PeruJurisdictionPack() if jurisdiction == "PE" else SpainJurisdictionPack()


def _generate_record(
    world: MasterDataWorld, jurisdiction: str, scenario: str, index: int, rng: random.Random,
    known_happy: list[CanonicalInvoice],
) -> tuple[CanonicalInvoice | None, CanonicalCreditNote | None, bytes | None]:
    pack = _pack_for(jurisdiction)
    company = next(c for c in world.companies if c.jurisdiction == jurisdiction)
    currency = "PEN" if jurisdiction == "PE" else "EUR"

    wants_withholding = scenario == "happy_path_with_withholding"
    supplier = next(
        s for s in world.suppliers
        if s.jurisdiction == jurisdiction
        and bool(s.profile.detraction_rate or s.profile.subject_to_irpf) == wants_withholding
    )

    products = [p for p in world.products if p.currency == currency]
    line_count = 5 if scenario == "multi_line" else 1
    chosen_products = (products * ((line_count // len(products)) + 1))[:line_count]

    series_number = f"F{jurisdiction}-{scenario}-{index:04d}"
    issue_date = date(2026, 1, 1) + timedelta(days=index % 300)

    invoice = build_invoice(pack, company, supplier, chosen_products, series_number, issue_date)

    if scenario == "wrong_tax_calculation":
        invoice = inject_wrong_tax_calculation(invoice)
    elif scenario == "missing_withholding":
        invoice = inject_missing_withholding(invoice)
    elif scenario == "invalid_tax_id":
        invoice = inject_invalid_tax_id(invoice)
    elif scenario == "multi_currency":
        foreign = "USD" if jurisdiction == "PE" else "GBP"
        rate = Decimal("3.75") if jurisdiction == "PE" else Decimal("0.85")
        invoice = inject_multi_currency(invoice, rate=rate, foreign_currency=foreign)
    elif scenario == "credit_note_full":
        return None, build_credit_note(invoice, scope="full"), None
    elif scenario == "credit_note_partial":
        return None, build_credit_note(invoice, scope="partial"), None
    elif scenario == "duplicate_pair":
        source = rng.choice(known_happy) if known_happy else invoice
        _, invoice = build_duplicate_pair(source)

    xml = degrade(pack.generate_xml(invoice), rng)
    return invoice, None, xml


def _dataset_checksum(out_dir: Path, manifest: list[DatasetRecord]) -> str:
    hasher = hashlib.sha256()
    hasher.update((out_dir / "manifest.json").read_bytes())
    for record in sorted(manifest, key=lambda r: r.record_id):
        for path in (record.invoice_json_path, record.xml_path, record.credit_note_json_path):
            if path is not None:
                hasher.update((out_dir / path).read_bytes())
    return hasher.hexdigest()


def generate_dataset(seed: int, out_dir: Path) -> dict:
    rng = random.Random(seed)
    world = generate_master_data(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[DatasetRecord] = []
    index = 0

    for split, counts in SCENARIO_COUNTS.items():
        (out_dir / split).mkdir(parents=True, exist_ok=True)
        known_happy: dict[str, list[CanonicalInvoice]] = {"PE": [], "ES": []}

        for scenario, count in counts.items():
            for _ in range(count):
                index += 1
                jurisdiction = "PE" if index % 2 == 0 else "ES"
                invoice, credit_note, xml = _generate_record(
                    world, jurisdiction, scenario, index, rng, known_happy[jurisdiction]
                )
                record_id = f"{split}-{scenario}-{index:05d}"

                invoice_json_path = xml_path = credit_note_json_path = None
                if invoice is not None:
                    invoice_json_path = f"{split}/{record_id}.invoice.json"
                    (out_dir / invoice_json_path).write_text(invoice.model_dump_json(indent=2))
                    if scenario in ("happy_path", "happy_path_with_withholding"):
                        known_happy[jurisdiction].append(invoice)
                if xml is not None:
                    xml_path = f"{split}/{record_id}.xml"
                    (out_dir / xml_path).write_bytes(xml)
                if credit_note is not None:
                    credit_note_json_path = f"{split}/{record_id}.credit_note.json"
                    (out_dir / credit_note_json_path).write_text(
                        credit_note.model_dump_json(indent=2)
                    )

                manifest.append(DatasetRecord(
                    record_id=record_id, split=split, jurisdiction=jurisdiction, scenario=scenario,
                    invoice_json_path=invoice_json_path, xml_path=xml_path,
                    credit_note_json_path=credit_note_json_path,
                ))

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps([asdict(r) for r in manifest], indent=2, sort_keys=True))

    checksum = _dataset_checksum(out_dir, manifest)
    (out_dir / "CHECKSUM").write_text(checksum + "\n")

    return {"total": len(manifest), "checksum": checksum, "manifest_path": str(manifest_path)}
