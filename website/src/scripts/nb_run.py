from nb_cli.cli import cli, run

"$ nb run --help\n" + run.get_help(
    run.make_context(
        "run",
        ["--help"],
        parent=cli.make_context("nb", []),
        resilient_parsing=True,
    )
)
