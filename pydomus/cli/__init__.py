import os
import typer
import pydomus.api
import argparse

state = argparse.Namespace()

show = typer.Typer()


@show.command()
def connectors():
    clist = state.ld.get_connectors()
    for c in clist:
        l = "{0[connector_key]}: {0[catg_clsid]} {0[label]}".format(c)
        typer.echo(l)

app = typer.Typer()
app.add_typer(show, name="show")

@app.callback()
def main_options(base_url=None, password=None):
    if base_url is None:
        base_url = os.environ.get("PYDOMUS_BASE_URL")
    if password is None:
        password = os.environ.get("PYDOMUS_PASSWORD")
    if base_url is None or password is None:
        typer.echo("Missing base URL or password", err=True)
        raise(SystemExit)

    state.base_url = base_url
    state.password = password
    state.ld = pydomus.api.LifeDomus(base_url, password)

def main():
    app()

if __name__ == "__main__":
    main()
