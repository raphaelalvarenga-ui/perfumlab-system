import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.legacy_data_migration import migration_cli


def main():
    parser = argparse.ArgumentParser(
        description="Migra datos JSON legacy de Perfum Lab a PostgreSQL."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Simula sin escribir.")
    mode.add_argument("--apply", action="store_true", help="Aplica migracion real.")
    parser.add_argument("--source", help="Ruta a la carpeta JSON fuente.", default=None)
    args = parser.parse_args()
    if not args.apply:
        args.dry_run = True
    migration_cli(args)


if __name__ == "__main__":
    main()
