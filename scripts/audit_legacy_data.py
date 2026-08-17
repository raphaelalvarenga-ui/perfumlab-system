import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.legacy_data_migration import inspect_source_cli


def main():
    parser = argparse.ArgumentParser(description="Audita JSON legacy de Perfum Lab.")
    parser.add_argument("--source", help="Ruta a la carpeta JSON fuente.", default=None)
    args = parser.parse_args()
    inspect_source_cli(args)


if __name__ == "__main__":
    main()
