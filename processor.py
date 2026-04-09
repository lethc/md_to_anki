# processor.py
# ── Lectura y preparación de la nota Markdown ─────────────────
# Lee el archivo .md, elimina metadatos de Obsidian y delega
# la generación de flashcards al módulo llm.

import re
from pathlib import Path

import frontmatter

import ui
from config import TARJETAS_POR_NOTA
from llm import generar_flashcards


def procesar_nota(
    ruta: Path,
    num_tarjetas: int = TARJETAS_POR_NOTA,
    debug: bool = False,
) -> list[dict]:
    """
    Lee un archivo .md, limpia los metadatos de Obsidian y genera
    las flashcards correspondientes. Retorna una lista de dicts con
    las claves 'pregunta', 'respuesta' y 'fuente'.
    """
    ui.seccion(f"Procesando: {ruta.name}")

    titulo, contenido = _leer_nota(ruta)
    contenido = _limpiar_metadatos(contenido)

    ui.info(f"Titulo detectado  : '{titulo}'")
    ui.info(f"Longitud contenido: {len(contenido)} caracteres")
    ui.info(f"Tarjetas a generar: {num_tarjetas}")

    if len(contenido.strip()) < 100:
        ui.skip(f"'{titulo}' tiene menos de 100 caracteres, se omite")
        return []

    if debug:
        ui.debug_line("Contenido tras limpiar frontmatter (primeros 500 chars):")
        print(f"\n  {contenido[:500]}\n")

    flashcards = generar_flashcards(contenido, titulo, num_tarjetas, debug=debug)
    ui.ok(f"{len(flashcards)} flashcards generadas exitosamente")

    for fc in flashcards:
        fc["fuente"] = titulo

    return flashcards


def _leer_nota(ruta: Path) -> tuple[str, str]:
    """
    Intenta leer el frontmatter YAML del archivo.
    Si falla, lee el archivo completo como texto plano.
    Retorna (titulo, contenido).
    """
    try:
        post = frontmatter.load(str(ruta))
        titulo = post.get("title", _titulo_desde_ruta(ruta))
        return titulo, post.content

    except Exception as e:
        ui.warn(f"No se pudo parsear frontmatter ({e}), leyendo archivo completo")
        contenido = ruta.read_text(encoding="utf-8")
        return _titulo_desde_ruta(ruta), contenido


def _limpiar_metadatos(contenido: str) -> str:
    """
    Elimina bloques YAML residuales (doble --- de Obsidian) y líneas
    de metadatos sueltos como Tags:, Source:, id:, aliases:.
    """
    # Cubre el caso del doble --- en notas de Obsidian
    contenido = re.sub(r"^---[\s\S]*?---", "", contenido, count=2).strip()

    # Líneas de metadatos que Obsidian deja fuera del frontmatter
    contenido = re.sub(
        r"^(Tags|Source|id|aliases|tags)\s*:.*$",
        "",
        contenido,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    return contenido


def _titulo_desde_ruta(ruta: Path) -> str:
    return ruta.stem.replace("-", " ").replace("_", " ")
