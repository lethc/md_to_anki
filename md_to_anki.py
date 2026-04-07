# md_to_anki.py
import ollama
import frontmatter
import re
import json
import argparse
import subprocess
import tempfile
import time
from pathlib import Path

# ── Configuración ─────────────────────────────────────────────
MODEL = "qwen3.5:0.8b"
TARJETAS_POR_NOTA = 5
APY_DECK = "Default"  # nombre del deck en Anki
APY_MODEL = "Basic"  # tipo de nota en Anki
APY_TAGS = ""  # etiquetas separadas por espacio, ej: "estudio python"
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
W = 60


def _line(char="-"):
    return char * W


def header(titulo: str):
    print(_line("="))
    print(f"  {titulo}")
    print(_line("="))


def seccion(titulo: str):
    print(f"\n  +-- {titulo.upper()} " + "-" * max(0, W - 8 - len(titulo)))


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


def resultado(msg: str):
    print(f"  [ DONE ]  {msg}")


def debug_line(msg: str):
    print(f"  [DEBUG]   {msg}")


def separador():
    print(f"  {_line('-')}")


# ──────────────────────────────────────────────────────────────


def limpiar_markdown(texto: str) -> str:
    # Eliminar bloques de código
    texto = re.sub(r"```[\s\S]*?```", "", texto)

    # Eliminar callouts de Obsidian >[!NOTE], >[!INFO], >[!WARNING], etc.
    texto = re.sub(r">\s*\[!.*?\].*", "", texto)

    # Eliminar wikilinks de Obsidian conservando texto de alias si existe
    # [[Página|Alias]] → Alias,  [[Página]] → Página
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

    # Eliminar numeración de listas  (1. 2. 3. etc.)
    texto = re.sub(r"^\s*\d+\.\s+", "", texto, flags=re.MULTILINE)

    # Eliminar viñetas de listas  (- * +)
    texto = re.sub(r"^\s*[-*+]\s+", "", texto, flags=re.MULTILINE)

    # Eliminar líneas horizontales ---
    texto = re.sub(r"^[-*_]{3,}\s*$", "", texto, flags=re.MULTILINE)

    # Eliminar líneas que solo tienen espacios o puntuación suelta
    texto = re.sub(r"^\s*[:\-\*]\s*$", "", texto, flags=re.MULTILINE)

    # Colapsar múltiples líneas vacías en una sola
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()


def generar_flashcards(
    contenido: str, titulo: str, n: int, debug: bool = False
) -> list[dict]:
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
    paso("Generando respuesta, por favor espera...")

    inicio = time.time()
    texto_completo = ""

    try:
        stream = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": prompt},
            ],
            options={
                "temperature": 0.3,
                "top_p": 0.9,
            },
            think=False,
            stream=True,
        )

        print("  [ RECV ]  Tokens: ", end="", flush=True)
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
    texto_completo = re.sub(r"<think>[\s\S]*?</think>", "", texto_completo).strip()

    if debug:
        debug_line("Respuesta raw del modelo (sin thinking):")
        print(f"\n{texto_completo}\n")

    try:
        texto_limpio = texto_completo.strip()
        texto_limpio = re.sub(r"^```json\s*", "", texto_limpio)
        texto_limpio = re.sub(r"\s*```$", "", texto_limpio)

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


def procesar_nota(
    ruta: Path, num_tarjetas: int = TARJETAS_POR_NOTA, debug: bool = False
) -> list[dict]:
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
    contenido = re.sub(r"^---[\s\S]*?---", "", contenido, count=2).strip()

    # Eliminar líneas de metadatos sueltos que Obsidian deja fuera del frontmatter
    contenido = re.sub(
        r"^(Tags|Source|id|aliases|tags)\s*:.*$",
        "",
        contenido,
        flags=re.MULTILINE | re.IGNORECASE,
    )

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


def flashcards_a_apy(flashcards: list[dict], deck: str, model: str, tags: str) -> str:
    """
    Convierte una lista de flashcards al formato markdown que apy espera.

    Formato por archivo:
        model: Basic
        deck: Default
        tags: mi-tag

        # Note

        ## Front
        ¿Pregunta?

        ## Back
        Respuesta.
        *Fuente: titulo-de-la-nota*
    """
    bloques = []

    # Cabecera global que apy leerá para todas las notas del archivo
    cabecera = f"model: {model}\ndeck: {deck}\ntags: {tags}"

    for fc in flashcards:
        pregunta = fc.get("pregunta", "").strip()
        respuesta = fc.get("respuesta", "").strip()
        fuente = fc.get("fuente", "").strip()

        bloque = f"# Note\n\n## Front\n\n{pregunta}\n\n## Back\n\n{respuesta}"

        if fuente:
            bloque += f"\n\n*Fuente: {fuente}*"

        bloques.append(bloque)

    return cabecera + "\n\n" + "\n\n".join(bloques) + "\n"


def enviar_con_apy(
    flashcards: list[dict],
    deck: str,
    model: str,
    tags: str,
    output: str | None,
    sync: bool,
    debug: bool,
):
    """
    Genera el archivo markdown para apy y lo envía con 'apy add-from-file'.
    Si output está definido, guarda también el archivo en esa ruta.
    Si sync es True, ejecuta 'apy sync' al terminar.
    """
    seccion("Generando archivo para apy")

    contenido_apy = flashcards_a_apy(flashcards, deck, model, tags)

    if debug:
        debug_line("Contenido del archivo apy:")
        print(contenido_apy)

    # Si el usuario pidió guardar el archivo, lo escribe en disco
    if output:
        ruta_out = Path(output)
        ruta_out.write_text(contenido_apy, encoding="utf-8")
        ok(f"Archivo guardado en: {ruta_out}")
        archivo_para_apy = str(ruta_out)
        tmp = None
    else:
        # Archivo temporal eliminado automáticamente al terminar
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        tmp.write(contenido_apy)
        tmp.flush()
        archivo_para_apy = tmp.name
        info(f"Archivo temporal: {archivo_para_apy}")

    seccion("Enviando flashcards a Anki via apy")

    try:
        cmd = ["apy", "add-from-file", archivo_para_apy]
        info(f"Ejecutando: {' '.join(cmd)}")
        resultado_cmd = subprocess.run(cmd, capture_output=True, text=True)

        if resultado_cmd.returncode == 0:
            ok("Flashcards añadidas correctamente a Anki")
            if resultado_cmd.stdout.strip():
                info(resultado_cmd.stdout.strip())
        else:
            error("apy reporto un error al añadir las notas")
            warn(resultado_cmd.stderr.strip() or "(sin mensaje de error)")

    except FileNotFoundError:
        error("El comando 'apy' no fue encontrado en el sistema")
        info("Instala apy con: pipx install apyanki")
        info("             o : uv tool install apyanki")
        if not output:
            info(f"El archivo generado sigue disponible en: {archivo_para_apy}")
        return

    finally:
        # Limpiar archivo temporal si no se pidió guardarlo
        if tmp:
            Path(tmp.name).unlink(missing_ok=True)

    # Sincronización opcional con AnkiWeb
    if sync:
        seccion("Sincronizando con AnkiWeb via apy")
        try:
            cmd_sync = ["apy", "sync"]
            info(f"Ejecutando: {' '.join(cmd_sync)}")
            resultado_sync = subprocess.run(cmd_sync, capture_output=True, text=True)

            if resultado_sync.returncode == 0:
                ok("Sincronizacion completada")
            else:
                warn("apy sync reporto un problema")
                warn(resultado_sync.stderr.strip() or "(sin mensaje)")

        except FileNotFoundError:
            error("No se pudo ejecutar 'apy sync'")


def main():
    parser = argparse.ArgumentParser(
        description="Convierte una nota Markdown a flashcards y las agrega a Anki via apy"
    )
    parser.add_argument(
        "archivo", type=str, help="Ruta al archivo .md que deseas convertir"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Guardar el archivo .md generado para apy en esta ruta (opcional)",
    )
    parser.add_argument(
        "-n",
        "--num-tarjetas",
        type=int,
        default=TARJETAS_POR_NOTA,
        help=f"Numero de flashcards a generar (default: {TARJETAS_POR_NOTA})",
    )
    parser.add_argument(
        "-d",
        "--deck",
        type=str,
        default=APY_DECK,
        help=f"Nombre del deck de Anki destino (default: '{APY_DECK}')",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=APY_MODEL,
        help=f"Tipo de nota de Anki (default: '{APY_MODEL}')",
    )
    parser.add_argument(
        "-t",
        "--tags",
        type=str,
        default=APY_TAGS,
        help="Etiquetas para las notas, separadas por espacio (default: ninguna)",
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

    ruta = Path(args.archivo)

    header("MD -> ANKI  //  Notas Markdown a Flashcards via apy")

    # Validaciones de archivo
    if not ruta.exists():
        error(f"Archivo no encontrado: {ruta}")
        return
    if ruta.suffix.lower() != ".md":
        error(f"El archivo debe tener extension .md: {ruta}")
        return

    # Verificar conexión con Ollama
    seccion("Verificando conexion con Ollama")
    try:
        modelos = ollama.list()
        nombres = [m.model for m in modelos.models]
        ok("Ollama activo")
        info(f"Modelos disponibles: {', '.join(nombres)}")
        if not any(MODEL in n for n in nombres):
            warn(f"El modelo '{MODEL}' no aparece en la lista")
            info(f"Descargalo con: ollama pull {MODEL}")
    except Exception as e:
        error(f"No se pudo conectar con Ollama: {e}")
        info("Inicia Ollama con: ollama serve")
        return

    # Verificar que apy está instalado (salvo en --dry-run)
    if not args.dry_run:
        seccion("Verificando instalacion de apy")
        try:
            r = subprocess.run(["apy", "--version"], capture_output=True, text=True)
            ok(f"apy encontrado: {r.stdout.strip() or 'version desconocida'}")
        except FileNotFoundError:
            error("El comando 'apy' no fue encontrado")
            info("Instala apy con : pipx install apyanki")
            info("             o  : uv tool install apyanki")
            return

    # Generar flashcards con el LLM
    inicio_total = time.time()
    flashcards = procesar_nota(ruta, num_tarjetas=args.num_tarjetas, debug=args.debug)

    if not flashcards:
        error("No se generaron flashcards. Usa --debug para mas detalles.")
        return

    # --dry-run: solo mostrar el archivo que se generaría sin enviarlo
    if args.dry_run:
        seccion("Dry-run: archivo que se enviaria a apy")
        print(flashcards_a_apy(flashcards, args.deck, args.model, args.tags))
        warn("Dry-run activo: no se envio nada a Anki")
    else:
        enviar_con_apy(
            flashcards=flashcards,
            deck=args.deck,
            model=args.model,
            tags=args.tags,
            output=args.output,
            sync=args.sync,
            debug=args.debug,
        )

    total = time.time() - inicio_total
    separador()
    resultado(f"Tiempo total: {total:.1f} segundos")
    print(_line("=") + "\n")

# Punto de Entrada del Script
if __name__ == "__main__":
    main()
