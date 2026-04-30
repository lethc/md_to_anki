# llm.py
# ── Interacción con el LLM via API externa ───────────

import json
import re
import time

import httpx

import ui
from cleaner import limpiar_markdown
from config import MODEL, API_KEY, API_URL, PROMPT_SISTEMA


def verificar_api() -> bool:
    """
    Verifica que la API key esté configurada y que el endpoint
    responda correctamente con una llamada mínima de prueba.
    """
    ui.seccion("Verificando conexion con la API")

    if not API_KEY or API_KEY == "sk-...":
        ui.error("API key no configurada en config.py")
        ui.info("Edita config.py y reemplaza el valor de API_KEY")
        return False

    try:
        body = {
            "model":      MODEL,
            "max_tokens": 16,
            "messages":   [{"role": "user", "content": "ping"}],
        }
        r = httpx.post(API_URL, headers=_headers(), json=body, timeout=15)
        r.raise_for_status()
        ui.ok(f"API accesible  : {API_URL}")
        ui.ok(f"Modelo en uso  : {MODEL}")
        return True

    except httpx.HTTPStatusError as e:
        ui.error(f"Error HTTP {e.response.status_code}: {e.response.text[:200]}")
        return False
    except Exception as e:
        ui.error(f"No se pudo conectar con la API: {e}")
        return False


# Alias para no tener que modificar main.py
verificar_ollama = verificar_api



# ── Generación de flashcards ───────────────────────────────────

def generar_flashcards(
    contenido: str,
    titulo: str,
    n: int,
    debug: bool = False,
) -> list[dict]:
    contenido_limpio = limpiar_markdown(contenido)

    if len(contenido_limpio) > 3000:
        contenido_limpio = contenido_limpio[:3000] + "..."

    if debug:
        ui.debug_line(f"Caracteres enviados al modelo: {len(contenido_limpio)}")
        ui.debug_line("Contenido limpio completo:")
        print(f"\n{contenido_limpio}\n")

    prompt = (
        f'Genera exactamente {n} flashcards sobre el siguiente tema: "{titulo}"\n\n'
        f"NOTAS:\n{contenido_limpio}\n\n"
        f"Recuerda: responde SOLO con el JSON, sin explicaciones adicionales."
    )

    ui.paso(f"Enviando prompt al modelo '{MODEL}'...")
    ui.paso("Generando respuesta, por favor espera...")

    texto = _llamar_modelo(prompt)

    if texto is None:
        return []

    if debug:
        ui.debug_line("Respuesta raw del modelo:")
        print(f"\n{texto}\n")

    return _parsear_json(texto, debug)


# ── Helpers privados ───────────────────────────────────────────

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "content-type":  "application/json",
    }


def _llamar_modelo(prompt: str) -> str | None:
    body = {
        "model":      MODEL,
        "max_tokens": 2048,
        "messages": [
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user",   "content": prompt},
        ],
    }

    inicio = time.time()
    try:
        r = httpx.post(API_URL, headers=_headers(), json=body, timeout=60)
        r.raise_for_status()

        datos   = r.json()
        texto   = datos["choices"][0]["message"]["content"]
        elapsed = time.time() - inicio

        tokens_entrada = datos.get("usage", {}).get("prompt_tokens",     "?")
        tokens_salida  = datos.get("usage", {}).get("completion_tokens", "?")

        ui.ok(
            f"Completado en {elapsed:.1f}s  "
            f"(in={tokens_entrada} / out={tokens_salida} tokens)"
        )
        return texto

    except httpx.HTTPStatusError as e:
        ui.error(f"Error HTTP {e.response.status_code}: {e.response.text[:300]}")
        return None
    except Exception as e:
        ui.error(f"Error llamando al modelo: {e}")
        return None


def _extraer_json(texto: str) -> str:
    """
    Extrae el bloque JSON de la respuesta del modelo de forma robusta.
    El modelo puede devolver el JSON envuelto en ```json ... ``` o suelto.
    No usa regex sobre el contenido completo para no cortar fences de código
    que estén dentro de los valores del JSON.
    """
    texto = texto.strip()

    # Caso 1: empieza directamente con { — JSON suelto
    if texto.startswith("{"):
        return texto

    # Caso 2: envuelto en ```json ... ```
    # Buscamos solo la primera línea de apertura y la última línea de cierre
    lineas = texto.splitlines()

    inicio = None
    for i, linea in enumerate(lineas):
        if linea.strip() in ("```json", "```"):
            inicio = i + 1
            break

    if inicio is None:
        return texto  # devolver tal cual y dejar que json.loads falle con buen mensaje

    # Buscar el cierre ``` desde el final hacia atrás
    fin = None
    for i in range(len(lineas) - 1, inicio - 1, -1):
        if lineas[i].strip() == "```":
            fin = i
            break

    if fin is None:
        return "\n".join(lineas[inicio:])  # sin cierre, tomamos hasta el final

    return "\n".join(lineas[inicio:fin])


def _parsear_json(texto: str, debug: bool) -> list[dict]:

    try:
        json_str   = _extraer_json(texto)
        datos      = json.loads(json_str)
        flashcards = datos.get("flashcards", [])

        if debug:
            ui.debug_line("Flashcards parseadas:")
            print(json.dumps(flashcards, indent=2, ensure_ascii=False))

        return flashcards

    except json.JSONDecodeError as e:
        ui.warn(f"Error parseando JSON: {e}")
        ui.debug_line("Respuesta que fallo al parsear:")
        print(f"  {texto[:500]}")
        return []
