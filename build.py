from babel.messages.frontend import CommandLineInterface


def build(src: str, dst: str):
    CommandLineInterface().run(
        ["pybabel", "compile", "-D", "nb-cli", "-d", "nb_cli/locale/"]
    )


if __name__ == "__main__":
    build("", "")
