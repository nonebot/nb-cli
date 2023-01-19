import anyio

from . import cli_main


def main(*args):
    anyio.run(cli_main, *args)


if __name__ == "__main__":
    main()
