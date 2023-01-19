from nb_cli.cli import cli, create

"$ nb create --help\n" + create.get_help(
    create.make_context(
        "create",
        ["--help"],
        parent=cli.make_context("nb", []),
        resilient_parsing=True,
    )
)
