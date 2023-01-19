from nb_cli.cli import cli, self

"$ nb self --help\n" + self.get_help(
    self.make_context(
        "self",
        ["--help"],
        parent=cli.make_context("nb", []),
        resilient_parsing=True,
    )
)
