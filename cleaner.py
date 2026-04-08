# cleaner.py
# ── Limpieza de contenido Markdown ────────────────────────────
# Elimina sintaxis de Markdown y patrones específicos de Obsidian
# para dejar solo el texto plano que el LLM necesita leer.

import re


def limpiar_markdown(texto: str) -> str:
    # Eliminar bloques de código
    texto = re.sub(r"```[\s\S]*?```", "", texto)

    # Eliminar callouts de Obsidian >[!NOTE], >[!INFO], >[!WARNING], etc.
    texto = re.sub(r">\s*\[!.*?\].*", "", texto)

    # Eliminar wikilinks conservando el alias si existe
    # [[Página|Alias]] → Alias  |  [[Página]] → Página
    texto = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", texto)
    texto = re.sub(r"\[\[([^\]]+)\]\]", r"\1", texto)

    # Eliminar imágenes markdown
    texto = re.sub(r"!\[.*?\]\(.*?\)", "", texto)

    # Eliminar links externos conservando el texto visible
    texto = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", texto)

    # Eliminar encabezados # conservando el texto
    texto = re.sub(r"^#{1,6}\s+", "", texto, flags=re.MULTILINE)

    # Eliminar negritas y cursivas conservando el texto
    texto = re.sub(r"\*{1,3}([^\*]+)\*{1,3}", r"\1", texto)
    texto = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", texto)

    # Eliminar numeración de listas (1. 2. 3. etc.)
    texto = re.sub(r"^\s*\d+\.\s+", "", texto, flags=re.MULTILINE)

    # Eliminar viñetas de listas (- * +)
    texto = re.sub(r"^\s*[-*+]\s+", "", texto, flags=re.MULTILINE)

    # Eliminar líneas horizontales ---
    texto = re.sub(r"^[-*_]{3,}\s*$", "", texto, flags=re.MULTILINE)

    # Eliminar líneas con solo puntuación suelta
    texto = re.sub(r"^\s*[:\-\*]\s*$", "", texto, flags=re.MULTILINE)

    # Colapsar múltiples líneas vacías en una sola
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()
