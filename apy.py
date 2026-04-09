# apy.py
# ── Integración con apy ───────────────────────────────────────
# Genera el archivo markdown en el formato que apy espera y
# lo envía a Anki usando 'apy add-from-file'. Opcionalmente
# sincroniza con AnkiWeb usando 'apy sync'.

import subprocess
import tempfile
from pathlib import Path

import ui


def verificar_apy() -> bool:
    """
    Comprueba que el comando 'apy' esté disponible en el sistema.
    Retorna True si está instalado.
    """
    ui.seccion("Verificando instalacion de apy")
    try:
        r = subprocess.run(["apy", "--version"], capture_output=True, text=True)
        ui.ok(f"apy encontrado: {r.stdout.strip() or 'version desconocida'}")
        return True
    except FileNotFoundError:
        ui.error("El comando 'apy' no fue encontrado")
        ui.info("Instala apy con : pipx install apyanki")
        ui.info("             o  : uv tool install apyanki")
        return False


def flashcards_a_apy(
    flashcards: list[dict],
    deck: str,
    model: str,
    tags: str,
) -> str:
    """
    Convierte una lista de flashcards al formato markdown que apy espera:

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
    cabecera = f"model: {model}\ndeck: {deck}\ntags: {tags}"
    bloques  = [_nota_a_bloque(fc) for fc in flashcards]
    return cabecera + "\n\n" + "\n\n".join(bloques) + "\n"


def enviar_con_apy(
    flashcards: list[dict],
    deck: str,
    model: str,
    tags: str,
    output: str | None,
    sync: bool,
    debug: bool,
) -> None:
    """
    Genera el archivo markdown para apy y lo envía con
    'apy add-from-file'. Si output está definido, guarda también
    el archivo en esa ruta. Si sync es True, ejecuta 'apy sync'.
    """
    ui.seccion("Generando archivo para apy")

    contenido_apy = flashcards_a_apy(flashcards, deck, model, tags)

    if debug:
        ui.debug_line("Contenido del archivo apy:")
        print(contenido_apy)

    archivo_para_apy, tmp = _preparar_archivo(contenido_apy, output)

    try:
        _ejecutar_add(archivo_para_apy, output)
        if sync:
            _ejecutar_sync()
    finally:
        if tmp:
            Path(tmp.name).unlink(missing_ok=True)


# ── Helpers privados ───────────────────────────────────────────

def _nota_a_bloque(fc: dict) -> str:
    pregunta  = fc.get("pregunta", "").strip()
    respuesta = fc.get("respuesta", "").strip()
    fuente    = fc.get("fuente", "").strip()

    bloque = f"# Note\n\n## Front\n\n{pregunta}\n\n## Back\n\n{respuesta}"

    if fuente:
        bloque += f"\n\n*Fuente: {fuente}*"

    return bloque


def _preparar_archivo(
    contenido: str,
    output: str | None,
) -> tuple[str, object]:
    """
    Escribe el contenido en disco. Si output está definido usa esa
    ruta; si no, crea un archivo temporal. Retorna (ruta, tmp_handle).
    """
    if output:
        ruta_out = Path(output)
        ruta_out.write_text(contenido, encoding="utf-8")
        ui.ok(f"Archivo guardado en: {ruta_out}")
        return str(ruta_out), None

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    )
    tmp.write(contenido)
    tmp.flush()
    ui.info(f"Archivo temporal: {tmp.name}")
    return tmp.name, tmp


def _ejecutar_add(archivo: str, output: str | None) -> None:
    ui.seccion("Enviando flashcards a Anki via apy")
    cmd = ["apy", "add-from-file", archivo]
    ui.info(f"Ejecutando: {' '.join(cmd)}")

    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            ui.ok("Flashcards añadidas correctamente a Anki")
            if r.stdout.strip():
                ui.info(r.stdout.strip())
        else:
            ui.error("apy reporto un error al añadir las notas")
            ui.warn(r.stderr.strip() or "(sin mensaje de error)")

    except FileNotFoundError:
        ui.error("El comando 'apy' no fue encontrado en el sistema")
        ui.info("Instala apy con: pipx install apyanki")
        if not output:
            ui.info(f"El archivo generado sigue disponible en: {archivo}")


def _ejecutar_sync() -> None:
    ui.seccion("Sincronizando con AnkiWeb via apy")
    cmd = ["apy", "sync"]
    ui.info(f"Ejecutando: {' '.join(cmd)}")

    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            ui.ok("Sincronizacion completada")
        else:
            ui.warn("apy sync reporto un problema")
            ui.warn(r.stderr.strip() or "(sin mensaje)")

    except FileNotFoundError:
        ui.error("No se pudo ejecutar 'apy sync'")
