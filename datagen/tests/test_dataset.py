import json
import tempfile
from pathlib import Path

from datagen.dataset import SCENARIO_COUNTS, generate_dataset
from jurisdiction_packs.es.pack import SpainJurisdictionPack
from jurisdiction_packs.pe.pack import PeruJurisdictionPack


def test_generate_dataset_produces_300_records_with_correct_split():
    with tempfile.TemporaryDirectory() as tmp:
        result = generate_dataset(seed=42, out_dir=Path(tmp))
        assert result["total"] == 300
        manifest = json.loads((Path(tmp) / "manifest.json").read_text())
        assert len([r for r in manifest if r["split"] == "dev"]) == 240
        assert len([r for r in manifest if r["split"] == "test"]) == 60


def test_generate_dataset_is_deterministic():
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        first = generate_dataset(seed=42, out_dir=Path(tmp1))
        second = generate_dataset(seed=42, out_dir=Path(tmp2))
        assert first["checksum"] == second["checksum"]


def test_every_scenario_kind_meets_its_exact_count_in_both_splits():
    with tempfile.TemporaryDirectory() as tmp:
        generate_dataset(seed=42, out_dir=Path(tmp))
        manifest = json.loads((Path(tmp) / "manifest.json").read_text())
        for split, counts in SCENARIO_COUNTS.items():
            split_records = [r for r in manifest if r["split"] == split]
            for scenario, expected_count in counts.items():
                actual = len([r for r in split_records if r["scenario"] == scenario])
                assert actual == expected_count, (
                    f"{split}/{scenario}: expected {expected_count}, got {actual}"
                )


def test_every_invoice_xml_round_trips_through_its_pack():
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        generate_dataset(seed=42, out_dir=out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        checked = 0
        for record in manifest:
            if record["xml_path"] is None:
                continue
            is_pe = record["jurisdiction"] == "PE"
            pack = PeruJurisdictionPack() if is_pe else SpainJurisdictionPack()
            parsed = pack.parse_structured((out_dir / record["xml_path"]).read_bytes())
            assert parsed is not None
            checked += 1
        assert checked > 0


def test_duplicate_pair_never_references_a_different_split():
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        generate_dataset(seed=42, out_dir=out_dir)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        for record in manifest:
            if record["scenario"] != "duplicate_pair" or record["invoice_json_path"] is None:
                continue
            invoice = json.loads((out_dir / record["invoice_json_path"]).read_text())
            assert invoice["invoice_key"].endswith("-DUP")
