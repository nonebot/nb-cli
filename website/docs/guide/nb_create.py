from importlib.metadata import entry_points

entry_points(name="nb", group="console_scripts")[0].load()(["nb", "create", "--help"])
