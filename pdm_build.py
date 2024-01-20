from babel.messages.frontend import CommandLineInterface


def pdm_build_initialize(context):
    CommandLineInterface().run(
        ["pybabel", "compile", "-D", "nb-cli", "-d", "nb_cli/locale/"]
    )
