# md_to_anki.py
import ollama
import genanki
import frontmatter
import re
import json
import argparse
import time
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────
# MODEL = "deepseek-r1:8b"
MODEL = "qwen3.5:0.8b"
TARJETAS_POR_NOTA = 5
# ──────────────────────────────────────────────────────────────

PROMPT_SISTEMA = """Eres un experto creando flashcards de estudio tipo Anki.
Tu tarea es leer un fragmento de notas y generar preguntas con sus respuestas.

REGLAS:
- Genera preguntas claras, concisas y específicas
- Las respuestas deben ser completas pero breves (1-3 oraciones)
- Enfócate en conceptos clave, definiciones y relaciones importantes
- Evita preguntas triviales o demasiado obvias
- Responde ÚNICAMENTE con JSON válido, sin texto adicional

FORMATO DE RESPUESTA (JSON estricto):
{
  "flashcards": [
    {"pregunta": "¿...?", "respuesta": "..."},
    {"pregunta": "¿...?", "respuesta": "..."}
  ]
}"""

# ── Utilidades de salida ASCII ─────────────────────────────────
W = 60  # ancho de los bloques

def _line(char="-"):
    return char * W

def header(titulo: str):
    print(_line("="))
    print(f"  {titulo}")
    print(_line("="))

def seccion(titulo: str):
    print(f"\n  +-- {titulo.upper()} " + "-" * (W - 8 - len(titulo)))

def ok(msg: str):
    print(f"  [  OK  ]  {msg}")

def info(msg: str):
    print(f"  [ INFO ]  {msg}")

def warn(msg: str):
    print(f"  [ WARN ]  {msg}")

def error(msg: str):
    print(f"  [  !!  ]  {msg}")

def skip(msg: str):
    print(f"  [ SKIP ]  {msg}")

def paso(msg: str):
    print(f"  [ >>>  ]  {msg}")

def progreso(msg: str):
    print(f"  [ .... ]  {msg}", end="\r", flush=True)

def resultado(msg: str):
    print(f"  [ DONE ]  {msg}")

def debug_line(msg: str):
    print(f"  [DEBUG]   {msg}")

def separador():
    print(f"  {_line('-')}")
# ──────────────────────────────────────────────────────────────


def limpiar_markdown(texto: str) -> str:
    # Eliminar bloques de código
    texto = re.sub(r'```[\s\S]*?```', '', texto)

    # Eliminar callouts de Obsidian >[!NOTE], >[!INFO], >[!WARNING], etc.
    texto = re.sub(r'>\s*\[!.*?\].*', '', texto)

    # Eliminar wikilinks de Obsidian conservando texto de alias si existe
    # [[Página|Alias]] → Alias,  [[Página]] → Página
    texto = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', texto)
    texto = re.sub(r'\[\[([^\]]+)\]\]', r'\1', texto)

    # Eliminar imágenes markdown
    texto = re.sub(r'!\[.*?\]\(.*?\)', '', texto)

    # Eliminar links externos conservando el texto visible
    texto = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', texto)

    # Eliminar encabezados # conservando el texto
    texto = re.sub(r'^#{1,6}\s+', '', texto, flags=re.MULTILINE)

    # Eliminar negritas y cursivas conservando el texto
    texto = re.sub(r'\*{1,3}([^\*]+)\*{1,3}', r'\1', texto)
    texto = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', texto)

    # Eliminar numeración de listas  (1. 2. 3. etc.)
    texto = re.sub(r'^\s*\d+\.\s+', '', texto, flags=re.MULTILINE)

    # Eliminar viñetas de listas  (- * +)
    texto = re.sub(r'^\s*[-*+]\s+', '', texto, flags=re.MULTILINE)

    # Eliminar líneas horizontales ---
    texto = re.sub(r'^[-*_]{3,}\s*$', '', texto, flags=re.MULTILINE)

    # Eliminar líneas que solo tienen espacios o puntuación suelta
    texto = re.sub(r'^\s*[:\-\*]\s*$', '', texto, flags=re.MULTILINE)

    # Colapsar múltiples líneas vacías en una sola
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    return texto.strip()


def generar_flashcards(contenido: str, titulo: str, n: int, debug: bool = False) -> list[dict]:
    contenido_limpio = limpiar_markdown(contenido)

    if len(contenido_limpio) > 3000:
        contenido_limpio = contenido_limpio[:3000] + "..."

    if debug:
        debug_line(f"Caracteres enviados al modelo: {len(contenido_limpio)}")
        debug_line("Contenido limpio completo:")
        print(f"\n{contenido_limpio}\n")

    prompt = f"""Genera exactamente {n} flashcards sobre el siguiente tema: "{titulo}"

NOTAS:
{contenido_limpio}

Recuerda: responde SOLO con el JSON, sin explicaciones adicionales."""

    paso(f"Enviando prompt al modelo '{MODEL}'...")
    paso(f"Generando respuesta, por favor espera...")

    inicio = time.time()
    texto_completo = ""

    try:
        stream = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user",   "content": prompt}
            ],
            options={
                "temperature": 0.3,
                "top_p": 0.9,
            },
            think=False,
            stream=True
        )

        print(f"  [ RECV ]  Tokens: ", end="", flush=True)
        token_count = 0

        for chunk in stream:
            token = chunk["message"]["content"]
            texto_completo += token
            token_count += 1
            if token_count % 10 == 0:
                print("#", end="", flush=True)

        elapsed = time.time() - inicio
        print(f"\n  [  OK  ]  Completado en {elapsed:.1f}s ({token_count} tokens)")

    except Exception as e:
        print()
        error(f"Error llamando al modelo: {e}")
        info("Verifica que Ollama este corriendo : ollama serve")
        info("Verifica que el modelo este descargado: ollama list")
        return []

    # Safety net: eliminar bloques <think> por si el modelo los genera igual
    texto_completo = re.sub(r'<think>[\s\S]*?</think>', '', texto_completo).strip()

    if debug:
        debug_line("Respuesta raw del modelo (sin thinking):")
        print(f"\n{texto_completo}\n")

    try:
        texto_limpio = texto_completo.strip()
        texto_limpio = re.sub(r'^```json\s*', '', texto_limpio)
        texto_limpio = re.sub(r'\s*```$', '', texto_limpio)

        datos = json.loads(texto_limpio)
        flashcards = datos.get("flashcards", [])

        if debug:
            debug_line("Flashcards parseadas:")
            print(json.dumps(flashcards, indent=2, ensure_ascii=False))

        return flashcards

    except json.JSONDecodeError as e:
        warn(f"Error parseando JSON: {e}")
        debug_line("Respuesta que fallo al parsear:")
        print(f"  {texto_completo[:500]}")
        return []


def procesar_nota(ruta: Path, num_tarjetas: int = TARJETAS_POR_NOTA, debug: bool = False) -> list[dict]:
    seccion(f"Procesando: {ruta.name}")

    # Intentar leer frontmatter YAML — si falla, leer el archivo completo
    try:
        post = frontmatter.load(str(ruta))
        titulo = post.get("title", ruta.stem.replace("-", " ").replace("_", " "))
        contenido = post.content
    except Exception as e:
        warn(f"No se pudo parsear frontmatter ({e}), leyendo archivo completo")
        contenido = ruta.read_text(encoding="utf-8")
        titulo = ruta.stem.replace("-", " ").replace("_", " ")

    # Eliminar bloques YAML residuales — cubre el doble --- de notas Obsidian
    contenido = re.sub(r'^---[\s\S]*?---', '', contenido, count=2).strip()

    # Eliminar líneas de metadatos sueltos que Obsidian deja fuera del frontmatter
    # como "Tags:", "Source:", "id:", "aliases:", etc.
    contenido = re.sub(r'^(Tags|Source|id|aliases|tags)\s*:.*$', '', contenido, flags=re.MULTILINE | re.IGNORECASE)

    info(f"Titulo detectado  : '{titulo}'")
    info(f"Longitud contenido: {len(contenido)} caracteres")
    info(f"Tarjetas a generar: {num_tarjetas}")

    if len(contenido.strip()) < 100:
        skip(f"'{titulo}' tiene menos de 100 caracteres, se omite")
        return []

    if debug:
        debug_line("Contenido tras limpiar frontmatter (primeros 500 chars):")
        print(f"\n  {contenido[:500]}\n")

    flashcards = generar_flashcards(contenido, titulo, num_tarjetas, debug=debug)
    ok(f"{len(flashcards)} flashcards generadas exitosamente")

    for fc in flashcards:
        fc["fuente"] = titulo

    return flashcards


def crear_deck_anki(todas_flashcards: list[dict], output: str):
    seccion(f"Creando deck Anki")
    info(f"Total de tarjetas: {len(todas_flashcards)}")

    deck_id   = 1_234_567_890
    modelo_id = 9_876_543_210

    modelo_tarjeta = genanki.Model(
        modelo_id,
        "Notas MD -> Anki",
        fields=[
            {"name": "Pregunta"},
            {"name": "Respuesta"},
            {"name": "Fuente"},
        ],
        templates=[{
            "name": "Tarjeta",
            "qfmt": """
                <div class='fuente'>{{Fuente}}</div>
                <div class='pregunta'>{{Pregunta}}</div>
            """,
            "afmt": """
                {{FrontSide}}
                <hr>
                <div class='respuesta'>{{Respuesta}}</div>
            """,
        }],
        css="""
            .card { font-family: 'Segoe UI', sans-serif; font-size: 16px;
                    text-align: left; padding: 20px; max-width: 600px; margin: auto; }
            .fuente { font-size: 11px; color: #888; margin-bottom: 8px;
                      text-transform: uppercase; letter-spacing: 1px; }
            .pregunta { font-size: 18px; font-weight: bold; color: #1a1a2e; }
            .respuesta { font-size: 15px; color: #2d4059; line-height: 1.6; }
            hr { border: none; border-top: 2px solid #e0e0e0; margin: 15px 0; }
        """
    )

    deck = genanki.Deck(deck_id, "Notas Personales")

    for i, fc in enumerate(todas_flashcards, 1):
        nota = genanki.Note(
            model=modelo_tarjeta,
            fields=[
                fc.get("pregunta", ""),
                fc.get("respuesta", ""),
                fc.get("fuente", ""),
            ]
        )
        deck.add_note(nota)
        if i % 5 == 0 or i == len(todas_flashcards):
            info(f"Tarjetas añadidas al deck: {i}/{len(todas_flashcards)}")

    genanki.Package(deck).write_to_file(output)
    separador()
    resultado(f"Archivo creado   : '{output}'")
    resultado(f"Siguiente paso   : Archivo -> Importar en Anki")


def main():
    parser = argparse.ArgumentParser(
        description="Convierte una nota Markdown a flashcards de Anki"
    )
    parser.add_argument(
        "archivo",
        type=str,
        help="Ruta al archivo .md que deseas convertir"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Nombre del archivo de salida .apkg (opcional)"
    )
    parser.add_argument(
        "-n", "--num-tarjetas",
        type=int,
        default=TARJETAS_POR_NOTA,
        help=f"Número de flashcards a generar (default: {TARJETAS_POR_NOTA})"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Muestra información detallada del proceso y respuesta del modelo"
    )
    args = parser.parse_args()

    ruta = Path(args.archivo)

    header("MD -> ANKI  //  Notas Markdown a Flashcards")

    # Validaciones de Archivo
    if not ruta.exists():
        error(f"Archivo no encontrado: {ruta}")
        return
    if ruta.suffix.lower() != ".md":
        error(f"El archivo debe tener extension .md: {ruta}")
        return

    # Verificar Conexión con Ollama
    seccion("Verificando conexion con Ollama")
    try:
        modelos = ollama.list()
        nombres = [m.model for m in modelos.models]
        ok(f"Ollama activo")
        info(f"Modelos disponibles: {', '.join(nombres)}")
        if not any(MODEL in n for n in nombres):
            warn(f"El modelo '{MODEL}' no aparece en la lista")
            info(f"Descargalo con: ollama pull {MODEL}")
    except Exception as e:
        error(f"No se pudo conectar con Ollama: {e}")
        info("Inicia Ollama con: ollama serve")
        return

    # Definir Nombre de Archivo de Salida
    # Si el usuario especificó -o nombre.apkg -> usa ese nombre
    # Si no -> genera automáticamente: nombre_del_archivo.md -> nombre_del_archivo.apkg
    output = args.output or ruta.stem + ".apkg"

    # Ejecución Principal con Medición de Tiempo
    inicio_total = time.time()
    flashcards = procesar_nota(ruta, num_tarjetas=args.num_tarjetas, debug=args.debug)

    if not flashcards:
        error("No se generaron flashcards. Usa --debug para mas detalles.")
        return

    crear_deck_anki(flashcards, output)

    total = time.time() - inicio_total
    separador()
    resultado(f"Tiempo total: {total:.1f} segundos")
    print(_line("=") + "\n")

# Punto de Entrada del Script
if __name__ == "__main__":
    main()
