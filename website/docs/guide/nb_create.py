import click

from nb_cli import cli_sync

print("run")
cli_sync(["nb", "create", "--help"])
print("done")

"$ nb create --help\n" + click.get_text_stream("stdout").read()
