from .card import Card as Card
from .gallery import Gallery as Gallery

if __name__ == "__main__":
    import asyncio

    from nb_cli.handlers.plugin import list_plugins

    app = Gallery()
    app.datasource = asyncio.run(list_plugins())
    app.run()
