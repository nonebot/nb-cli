from nb_cli.cli import cli, adapter

"$ nb adapter --help\n" + adapter.get_help(
    adapter.make_context(
        "adapter",
        ["--help"],
        parent=cli.make_context("nb", []),
        resilient_parsing=True,
    )
)
