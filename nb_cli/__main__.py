import sys

import anyio

from . import cli_main


def main(*args):
    try:
        anyio.run(cli_main, *args)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
