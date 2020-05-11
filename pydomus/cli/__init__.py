import os
import typer
import pydomus.api
import argparse
import xlrd

state = argparse.Namespace()

### SHOW ###

show = typer.Typer()

@show.command()
def connectors():
    clist = state.ld.get_connectors()
    for c in clist:
        l = "{0[connector_key]} {0[catg_clsid]:<40} {0[label]}".format(c)
        typer.echo(l)


@show.command()
def rooms():
    rlist = state.ld.get_rooms()
    for r in rlist:
        l = "{0[room_key]} {0[label]}".format(r)
        typer.echo(l)


@show.command()
def domains():
    domlist = state.ld.get_domains()
    for dom,catlist in domlist.values():
        typer.echo( "{0[domn_clsid]}: {0[label]}".format(dom) )
        for cat,devlist in catlist.values():
            typer.echo( "    {0[catg_clsid]}: {0[label]}".format(cat) )
            for dev in devlist.values():
                typer.echo( "        {0[devc_clsid]}: {0[label]}".format(dev) )

@show.command()
def devices():
    devlist = state.ld.get_devices()
    for d in sorted(devlist, key=lambda x:x["devc_clsid"]):
        typer.echo( "{0[device_key]} {0[devc_clsid]} {0[label]:<40} {0[room_label]}" .format(d) )

@show.command()
def device(device:str):
    d = state.ld.get_device(device)
    typer.echo("%r" % d)

@show.command()
def properties(dev):
    if not dev.startswith("DEVC_00") and len(dev) != 40:
        dev = state.ld.get_device_key(dev)
    proplist = state.ld.get_device_properties(dev)
    for p in proplist:
        typer.echo( "{0[prop_clsid]:<40} {0[refr_ctrl]!s:<8} {0[refr_indc]!s:<8} {0[label]}" .format(p) )

### ADD ###

add = typer.Typer()

@add.command()
def knx_light(label, room, write_cmd, read_cmd):
    state.ld.add_knx_light(label, room, write_cmd, read_cmd)


@add.command()
def knx_dimmer(label, room, write_cmd, read_cmd, write_val, read_val):
    state.ld.add_knx_dimmer(label, room, write_cmd, read_cmd, write_val, read_val)




### MAIN ###

app = typer.Typer()
app.add_typer(show, name="show")
app.add_typer(add, name="add")

@app.callback()
def main_options(base_url=None,
                 password=None,
                 no_verify:bool=typer.Option(False, "--insecure", "-k",
                                             help="Do not verify certificate")):
    if base_url is None:
        base_url = os.environ.get("PYDOMUS_BASE_URL")
    if password is None:
        password = os.environ.get("PYDOMUS_PASSWORD")
    if base_url is None or password is None:
        typer.echo("Missing base URL or password", err=True)
        raise(SystemExit)

    state.base_url = base_url
    state.password = password
    if no_verify:
        import warnings
        warnings.filterwarnings("ignore")
    state.ld = pydomus.api.LifeDomus(base_url, password, not no_verify)

def main():
    app()

if __name__ == "__main__":
    main()
