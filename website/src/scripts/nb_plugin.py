from nb_cli.cli import cli, plugin

"$ nb plugin --help\n" + plugin.get_help(
    plugin.make_context(
        "plugin",
        ["--help"],
        parent=cli.make_context("nb", []),
        resilient_parsing=True,
    )
)
