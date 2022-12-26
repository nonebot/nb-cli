import anyio

from . import cli_main


def main():
    anyio.run(cli_main)


if __name__ == "__main__":
    main()
