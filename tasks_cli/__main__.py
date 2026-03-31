"""Punto de entrada — permite ejecutar con: python -m tasks_cli"""


def main() -> None:
    # Inicializar el idioma ANTES de importar cli.main para que los
    # textos help= de Typer se generen en el idioma correcto.
    from tasks_cli.config import get_config
    from tasks_cli.i18n import set_language

    set_language(get_config().language)

    from tasks_cli.cli.main import app

    app()


if __name__ == "__main__":
    main()
