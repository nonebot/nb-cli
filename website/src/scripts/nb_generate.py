from nb_cli.cli import cli, generate

"$ nb generate --help\n" + generate.get_help(
    generate.make_context(
        "generate",
        ["--help"],
        parent=cli.make_context("nb", []),
        resilient_parsing=True,
    )
)
