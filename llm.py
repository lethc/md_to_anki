# llm.py
# ── Interacción con el LLM local via Ollama ───────────────────

import json
import re
import subprocess
import time

import ollama

import ui
from cleaner import limpiar_markdown
from config import MODEL, PROMPT_SISTEMA

# Variable global para controlar si iniciamos Ollama
_ollama_iniciado_por_nosotros = False


def verificar_ollama() -> bool:
    """Verifica Ollama, lo inicia si es necesario."""
    ui.seccion("Verificando conexion con Ollama")
    
    # Intenta conectar
    if _conectar_ollama():
        return True
    
    # Si falla, intenta iniciar Ollama
    ui.info("Ollama no responde, intentando iniciar...")
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Para que corra en background
        )
        time.sleep(3)  # Espera a que arranque
        
        if _conectar_ollama():
            global _ollama_iniciado_por_nosotros
            _ollama_iniciado_por_nosotros = True
            ui.ok("Ollama iniciado correctamente")
            return True
        else:
            ui.error("No se pudo iniciar Ollama")
            return False
            
    except FileNotFoundError:
        ui.error("Comando 'ollama' no encontrado")
        return False


def _conectar_ollama() -> bool:
    """Intenta conectar con Ollama."""
    try:
        modelos = ollama.list()
        nombres = [m.model for m in modelos.models]
        ui.ok("Ollama activo")
        ui.info(f"Modelos disponibles: {', '.join(nombres)}")
        
        if not any(MODEL in n for n in nombres):
            ui.warn(f"El modelo '{MODEL}' no aparece en la lista")
            ui.info(f"Descargalo con: ollama pull {MODEL}")
        return True
    except Exception:
        return False


def cerrar_ollama() -> None:
    """Cierra Ollama si fue iniciado por nosotros."""
    global _ollama_iniciado_por_nosotros
    if _ollama_iniciado_por_nosotros:
        ui.seccion("Cerrando Ollama")
        try:
            subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True)
            ui.ok("Ollama detenido")
        except Exception:
            ui.warn("No se pudo detener Ollama")
        _ollama_iniciado_por_nosotros = False


# Resto del código original sin cambios...
def generar_flashcards(contenido: str, titulo: str, n: int, debug: bool = False) -> list[dict]:
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
    texto_completo = _llamar_modelo(prompt)
    if texto_completo is None:
        return []
    if debug:
        ui.debug_line("Respuesta raw del modelo (sin thinking):")
        print(f"\n{texto_completo}\n")
    return _parsear_json(texto_completo, debug)


def _llamar_modelo(prompt: str) -> str | None:
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
        ui.error(f"Error llamando al modelo: {e}")
        ui.info("Verifica que Ollama este corriendo : ollama serve")
        ui.info("Verifica que el modelo este descargado: ollama list")
        return None
    return re.sub(r"<think>[\s\S]*?</think>", "", texto_completo).strip()


def _parsear_json(texto: str, debug: bool) -> list[dict]:
    try:
        texto = texto.strip()
        texto = re.sub(r"^```json\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
        datos = json.loads(texto)
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
