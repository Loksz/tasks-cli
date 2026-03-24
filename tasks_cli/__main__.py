"""Punto de entrada — permite ejecutar con: python -m tasks_cli"""

from tasks_cli.cli.main import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
