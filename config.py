# config.py
# ── Configuración global ───────────────────────────────────────
# Cambia estos valores según tus preferencias.

MODEL             = "qwen3.5:0.8b"  # modelo Ollama a usar
TARJETAS_POR_NOTA = 5                 # flashcards generadas por nota
APY_DECK          = "Default"         # deck de destino en Anki
APY_MODEL         = "Basic"           # tipo de nota en Anki
APY_TAGS          = ""                # etiquetas separadas por espacio

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
