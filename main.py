import argparse
import logging
import sys

from scripts import ingesters as ig
from scripts.cache import clear_cache

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

ENTITY_MAP = {
    "drivers":      ig.ingest_all_drivers,
    "constructors": ig.ingest_all_constructors,
    "circuits":     ig.ingest_all_circuits,
    "races":        ig.ingest_all_races,
    "statuses":     ig.ingest_all_statuses,
    "results":      ig.ingest_all_results,
    "qualifying":   ig.ingest_qualifying,
    "pitstops":     ig.ingest_pit_stops,
}

RUN_ORDER = [
    "drivers", "constructors", "circuits", "statuses",
    "races", "results", "qualifying", "pitstops",
]


def run_entity(name: str) -> None:
    fn = ENTITY_MAP.get(name)
    if fn is None:
        logger.error("Entidad desconocida: %s", name)
        sys.exit(1)
    logger.info("--- Iniciando ingesta: %s ---", name)
    fn()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="F1 Historical Data Pipeline - CLI de ingesta",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all", action="store_true",
        help="Ejecuta TODAS las entidades en orden de dependencia",
    )
    group.add_argument(
        "--entity", type=str, choices=list(ENTITY_MAP.keys()),
        help="Ejecuta la ingesta de una sola entidad",
    )
    group.add_argument(
        "--list", action="store_true",
        help="Muestra las entidades disponibles y sale",
    )
    group.add_argument(
        "--clear-cache", action="store_true",
        help="Elimina todo el cache local de la API",
    )
    args = parser.parse_args()

    if args.list:
        print("Entidades disponibles:")
        for name in RUN_ORDER:
            print(f"  - {name}")
        sys.exit(0)

    if not args.all and not args.entity and not args.clear_cache:
        parser.error("Se requiere --all, --entity, --list o --clear-cache")

    if args.clear_cache:
        clear_cache()
        logger.info("Cache eliminado correctamente.")
        sys.exit(0)

    if args.all:
        logger.info("=== Ingesta completa iniciada ===")
        for name in RUN_ORDER:
            run_entity(name)
        logger.info("=== Ingesta completa finalizada ===")
    else:
        run_entity(args.entity)


if __name__ == "__main__":
    main()
