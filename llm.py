# llm.py
# ── Interacción con el LLM local via Ollama ───────────────────
# Verifica la conexión con Ollama y genera las flashcards
# enviando el contenido limpio al modelo configurado.

import json
import re
import time

import ollama

import logger
from cleaner import limpiar_markdown
from config import MODEL, PROMPT_SISTEMA


def verificar_ollama() -> bool:
    """
    Comprueba que Ollama esté activo y que el modelo configurado
    esté disponible. Retorna True si todo está en orden.
    """
    logger.seccion("Verificando conexion con Ollama")
    try:
        modelos = ollama.list()
        nombres = [m.model for m in modelos.models]
        logger.ok("Ollama activo")
        logger.info(f"Modelos disponibles: {', '.join(nombres)}")

        if not any(MODEL in n for n in nombres):
            logger.warn(f"El modelo '{MODEL}' no aparece en la lista")
            logger.info(f"Descargalo con: ollama pull {MODEL}")

        return True

    except Exception as e:
        logger.error(f"No se pudo conectar con Ollama: {e}")
        logger.info("Inicia Ollama con: ollama serve")
        return False


def generar_flashcards(
    contenido: str,
    titulo: str,
    n: int,
    debug: bool = False,
) -> list[dict]:
    """
    Envía el contenido limpio al LLM y retorna una lista de dicts
    con las claves 'pregunta' y 'respuesta'.
    """
    contenido_limpio = limpiar_markdown(contenido)

    if len(contenido_limpio) > 3000:
        contenido_limpio = contenido_limpio[:3000] + "..."

    if debug:
        logger.debug_line(f"Caracteres enviados al modelo: {len(contenido_limpio)}")
        logger.debug_line("Contenido limpio completo:")
        print(f"\n{contenido_limpio}\n")

    prompt = (
        f'Genera exactamente {n} flashcards sobre el siguiente tema: "{titulo}"\n\n'
        f"NOTAS:\n{contenido_limpio}\n\n"
        f"Recuerda: responde SOLO con el JSON, sin explicaciones adicionales."
    )

    logger.paso(f"Enviando prompt al modelo '{MODEL}'...")
    logger.paso("Generando respuesta, por favor espera...")

    texto_completo = _llamar_modelo(prompt)
    if texto_completo is None:
        return []

    if debug:
        logger.debug_line("Respuesta raw del modelo (sin thinking):")
        print(f"\n{texto_completo}\n")

    return _parsear_json(texto_completo, debug)


def _llamar_modelo(prompt: str) -> str | None:
    """
    Realiza el streaming de la respuesta del modelo y retorna
    el texto completo. Retorna None si ocurre un error.
    """
    texto_completo = ""
    inicio = time.time()

    try:
        stream = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user",   "content": prompt},
            ],
            options={"temperature": 0.3, "top_p": 0.9},
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
        logger.error(f"Error llamando al modelo: {e}")
        logger.info("Verifica que Ollama este corriendo : ollama serve")
        logger.info("Verifica que el modelo este descargado: ollama list")
        return None

    # Safety net: eliminar bloques <think> por si el modelo los genera igual
    return re.sub(r"<think>[\s\S]*?</think>", "", texto_completo).strip()


def _parsear_json(texto: str, debug: bool) -> list[dict]:
    """
    Extrae y parsea el JSON de la respuesta del modelo.
    Retorna una lista vacía si el parseo falla.
    """
    try:
        texto = texto.strip()
        texto = re.sub(r"^```json\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)

        datos = json.loads(texto)
        flashcards = datos.get("flashcards", [])

        if debug:
            logger.debug_line("Flashcards parseadas:")
            print(json.dumps(flashcards, indent=2, ensure_ascii=False))

        return flashcards

    except json.JSONDecodeError as e:
        logger.warn(f"Error parseando JSON: {e}")
        logger.debug_line("Respuesta que fallo al parsear:")
        print(f"  {texto[:500]}")
        return []
