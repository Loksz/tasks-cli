"""Punto de entrada - permite ejecutar con: python -m tasks_cli"""

import io
import sys


def _ensure_utf8() -> None:
    """Fuerza UTF-8 en stdout/stderr en Windows para evitar errores de encoding."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        else:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        else:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def main() -> None:
    _ensure_utf8()
    # Inicializar el idioma ANTES de importar cli.main para que los
    # textos help= de Typer se generen en el idioma correcto.
    from tasks_cli.config import get_config
    from tasks_cli.i18n import set_language

    set_language(get_config().language)

    from tasks_cli.cli.main import app

    app()


if __name__ == "__main__":
    main()
