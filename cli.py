# cli.py
# ── Interfaz de línea de comandos ─────────────────────────────
# Define y parsea todos los argumentos del script.
# Separado de la lógica principal para facilitar pruebas
# y futuros cambios en la interfaz.

import argparse
from dataclasses import dataclass

from config import APY_DECK, APY_MODEL, APY_TAGS, TARJETAS_POR_NOTA


@dataclass
class Argumentos:
    """Contenedor tipado de todos los argumentos del CLI."""
    archivo:      str
    output:       str | None
    num_tarjetas: int
    deck:         str
    model:        str
    tags:         str
    sync:         bool
    dry_run:      bool
    debug:        bool


def parsear_argumentos() -> Argumentos:
    parser = argparse.ArgumentParser(
        description="Convierte una nota Markdown a flashcards y las agrega a Anki via apy",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "archivo",
        type=str,
        help="Ruta al archivo .md que deseas convertir",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Guardar el archivo .md generado para apy en esta ruta (opcional)",
    )
    parser.add_argument(
        "-n", "--num-tarjetas",
        type=int,
        default=TARJETAS_POR_NOTA,
        help=f"Numero de flashcards a generar (default: {TARJETAS_POR_NOTA})",
    )
    parser.add_argument(
        "-d", "--deck",
        type=str,
        default=APY_DECK,
        help=f"Nombre del deck de Anki destino (default: '{APY_DECK}')",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=APY_MODEL,
        help=f"Tipo de nota de Anki (default: '{APY_MODEL}')",
    )
    parser.add_argument(
        "-t", "--tags",
        type=str,
        default=APY_TAGS,
        help="Etiquetas separadas por espacio (default: ninguna)",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Ejecutar 'apy sync' para sincronizar con AnkiWeb al terminar",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Genera y muestra el archivo apy pero NO lo envia a Anki",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Muestra informacion detallada del proceso y respuesta del modelo",
    )

    args = parser.parse_args()

    return Argumentos(
        archivo      = args.archivo,
        output       = args.output,
        num_tarjetas = args.num_tarjetas,
        deck         = args.deck,
        model        = args.model,
        tags         = args.tags,
        sync         = args.sync,
        dry_run      = args.dry_run,
        debug        = args.debug,
    )
