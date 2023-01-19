from nb_cli.cli import cli, driver

"$ nb driver --help\n" + driver.get_help(
    driver.make_context(
        "driver",
        ["--help"],
        parent=cli.make_context("nb", []),
        resilient_parsing=True,
    )
)
