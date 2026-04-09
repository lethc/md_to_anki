# ui.py
# ── Utilidades de salida ASCII ─────────────────────────────────
# Todas las funciones de impresión en consola están aquí
# centralizadas para facilitar cambios de estilo.

W = 60  # ancho de los bloques


def _line(char: str = "-") -> str:
    return char * W


def header(titulo: str) -> None:
    print(_line("="))
    print(f"  {titulo}")
    print(_line("="))


def seccion(titulo: str) -> None:
    relleno = "-" * max(0, W - 8 - len(titulo))
    print(f"\n  +-- {titulo.upper()} {relleno}")


def ok(msg: str) -> None:
    print(f"  [  OK  ]  {msg}")


def info(msg: str) -> None:
    print(f"  [ INFO ]  {msg}")


def warn(msg: str) -> None:
    print(f"  [ WARN ]  {msg}")


def error(msg: str) -> None:
    print(f"  [  !!  ]  {msg}")


def skip(msg: str) -> None:
    print(f"  [ SKIP ]  {msg}")


def paso(msg: str) -> None:
    print(f"  [ >>>  ]  {msg}")


def resultado(msg: str) -> None:
    print(f"  [ DONE ]  {msg}")


def debug_line(msg: str) -> None:
    print(f"  [DEBUG]   {msg}")


def separador() -> None:
    print(f"  {_line('-')}")


def linea_final() -> None:
    print(_line("=") + "\n")
