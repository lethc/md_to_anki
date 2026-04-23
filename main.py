# main.py
# ── Punto de entrada ──────────────────────────────────────────
# Orquesta el flujo completo del programa sin contener
# lógica de negocio. Cada paso delega en su módulo.
#
# Uso:
#   python -m md_to_anki nota.md
#   python -m md_to_anki nota.md -n 8 -d "Mi Deck" -t "java" --sync
#   python -m md_to_anki nota.md --dry-run

import time
from pathlib import Path

import ui
from apy import enviar_con_apy, flashcards_a_apy, verificar_apy
from cli import parsear_argumentos
from llm import verificar_api, generar_flashcards
from processor import procesar_nota


def main() -> None:
    args = parsear_argumentos()
    ruta = Path(args.archivo)

    ui.header("MD -> ANKI  //  Notas Markdown a Flashcards via apy")

    # ── Validaciones previas ───────────────────────────────────
    if not ruta.exists():
        ui.error(f"Archivo no encontrado: {ruta}")
        return

    if ruta.suffix.lower() != ".md":
        ui.error(f"El archivo debe tener extension .md: {ruta}")
        return

    if not verificar_api():
        return

    if not args.dry_run and not verificar_apy():
        return

    # ── Generación de flashcards ───────────────────────────────
    inicio_total = time.time()

    flashcards = procesar_nota(
        ruta         = ruta,
        num_tarjetas = args.num_tarjetas,
        debug        = args.debug,
    )

    if not flashcards:
        ui.error("No se generaron flashcards. Usa --debug para mas detalles.")
        return

    # ── Envío a Anki o dry-run ─────────────────────────────────
    if args.dry_run:
        ui.seccion("Dry-run: archivo que se enviaria a apy")
        print(flashcards_a_apy(flashcards, args.deck, args.model, args.tags))
        ui.warn("Dry-run activo: no se envio nada a Anki")
    else:
        enviar_con_apy(
            flashcards = flashcards,
            deck       = args.deck,
            model      = args.model,
            tags       = args.tags,
            output     = args.output,
            sync       = args.sync,
            debug      = args.debug,
        )

    # ── Resumen final ──────────────────────────────────────────
    total = time.time() - inicio_total
    ui.separador()
    ui.resultado(f"Tiempo total: {total:.1f} segundos")
    ui.linea_final()


if __name__ == "__main__":
    main()
