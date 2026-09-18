import argparse
from pathlib import Path

from datagen.dataset import generate_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the FlowForge synthetic invoice dataset")
    parser.add_argument("command", choices=["generate"])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/v0.1"))
    args = parser.parse_args()

    result = generate_dataset(seed=args.seed, out_dir=args.out)
    print(f"Generated {result['total']} records in {args.out}")
    print(f"Checksum: {result['checksum']}")


if __name__ == "__main__":
    main()
