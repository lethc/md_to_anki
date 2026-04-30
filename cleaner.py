# cleaner.py
# ── Limpieza de contenido Markdown ────────────────────────────
# Elimina sintaxis de Markdown y patrones específicos de Obsidian
# para dejar solo el texto plano que el LLM necesita leer.
# Los bloques de código se conservan intactos, incluyendo sus
# comentarios internos, para que el modelo pueda generar
# flashcards sobre ellos.

import re


def limpiar_markdown(texto: str) -> str:
    # ── Paso 1: extraer y proteger bloques de código ───────────
    # Los guardamos temporalmente para que las reglas de limpieza
    # posteriores no toquen su contenido (ej: # dentro de Python/bash
    # no debe tratarse como encabezado Markdown).
    bloques_codigo = {}
    contador = [0]

    def guardar_bloque(m):
        clave = f"\x00CODEBLOCK{contador[0]}\x00"
        bloques_codigo[clave] = m.group(0)
        contador[0] += 1
        return clave

    texto = re.sub(r"```[\s\S]*?```", guardar_bloque, texto)

    # ── Paso 2: limpieza normal de Markdown/Obsidian ───────────

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
    # (solo aplica fuera de bloques de código gracias al paso 1)
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

    # ── Paso 3: restaurar bloques de código ───────────────────
    for clave, bloque in bloques_codigo.items():
        texto = texto.replace(clave, bloque)

    return texto.strip()
