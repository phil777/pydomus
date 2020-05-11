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

@show.command("room")
def show_room(room:str):
    typer.echo(state.ld.get_room(room))


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

@add.command("room")
def add_room(clsid, label):
    typer.echo(state.ld.add_room(clsid, label))

@add.command()
def knx_light(label, room, write_cmd, read_cmd):
    state.ld.add_knx_light(label, room, write_cmd, read_cmd)


@add.command()
def knx_dimmer(label, room, write_cmd, read_cmd, write_val, read_val):
    state.ld.add_knx_dimmer(label, room, write_cmd, read_cmd, write_val, read_val)


### DELETE ###

delete = typer.Typer()

@delete.command("device")
def del_device(device:str):
    if not state.ld.delete_device(device):
        typer.echo("failed", err=True)

@delete.command("room")
def del_room(room:str):
    if not state.ld.delete_room(room):
        typer.echo("failed", err=True)

### PROVISION ###

provision = typer.Typer()

@provision.command("rooms")
def prov_rooms(excel_file, sheet="LD Rooms"):
    wb = xlrd.open_workbook(excel_file)
    sh = wb.sheet_by_name(sheet)
    for rowx in range(1, sh.nrows):
        label = sh.cell_value(rowx, 0)
        rtype = sh.cell_value(rowx, 1)
        pic = sh.cell_value(rowx, 2)
        typer.echo("Creating [%s] as type [%s]" % (label,rtype))
        room = state.ld.add_room(rtype, label)
        if pic:
            state.ld.set_room_picture(room, pic)

@provision.command("devices")
def prov_devices(connector:str, excel_file:str, sheets:str=""):
    wb = xlrd.open_workbook(excel_file)
    if sheets:
        sheets = sheets.split(",")
    else:
        sheets = [ sn for sn in wb.sheet_names() if sn.startswith("LD CLSID")]

    for sheet_name in sheets:
        sh = wb.sheet_by_name(sheet_name)
        _,clsid_lbl = sheet_name.split()
        clsid = state.ld.get_device_class_from_label(clsid_lbl)
        typer.echo(clsid)
        setprop = []
        propname = []
        for colx in range(3,sh.ncols):
            try:
                v = sh.cell_value(0, colx)
                prop,rw = v.split()
                prop = "CLSID-DEVC-PROP-"+prop
                if rw == "write":
                    f = lambda dev, ref, prop=prop: state.ld.set_device_property_ctrl(dev, prop, ref)
                    pn = "%s ctrl" % prop
                else:
                    f = lambda dev, ref, prop=prop: state.ld.set_device_property_indc(dev, prop, ref)
                    pn = "%s indc" % prop
                setprop.append(f)
                propname.append(pn)
            except Exception as e:
                raise Exception("Reading cell row=%i col=%i: %s" % (0,colx,e))
        for rowx in range(1, sh.nrows):
            devlabel = sh.cell_value(rowx,0)
            room = sh.cell_value(rowx,1)
            pic =  sh.cell_value(rowx,2)
            typer.echo("    Creating %s in %s" % (devlabel, room))
            dev=state.ld.add_device(clsid, sh.cell_value(rowx,0), sh.cell_value(rowx,1), connector)
            if pic:
                typer.echo("        setting pic %s" % pic)
                state.ld.set_device_picture(dev, pic)
            for colx in range(3, sh.ncols):
                ref = sh.cell_value(rowx, colx)
                ref_label = sh.cell_value(1, colx)
                if ref:
                    print("        {0:<40} = {1}".format(propname[colx-3],ref))
                    setprop[colx-3](dev, ref)



### UNPROVISION ###

unprovision = typer.Typer()

@unprovision.command("devices")
def unprov_devices(excel_file:str, sheets:str="", interactive:bool=False):
    wb = xlrd.open_workbook(excel_file)
    if sheets:
        sheets = sheets.split(",")
    else:
        sheets = [ sn for sn in wb.sheet_names() if sn.startswith("LD CLSID")]

    idev = {}
    devlist = state.ld.get_devices()
    for d in state.ld.get_devices():
        idev[d["label"], d["room_label"]] = d["device_key"]


    for sheet_name in sheets:
        sh = wb.sheet_by_name(sheet_name)
        _,clsid_lbl = sheet_name.split()
        clsid = state.ld.get_device_class_from_label(clsid_lbl)
        typer.echo(clsid)

        for rowx in range(1, sh.nrows):
            devlabel = sh.cell_value(rowx,0)
            room = sh.cell_value(rowx,1)
            k = (devlabel, room)
            if k in idev:
                typer.echo("Deleting %s (%s in %s)" % (idev[k], devlabel, room))
                if interactive:
                    r = input("ok?")
                    if r.lower() not in ["y","yes"]:
                        continue
                    typer.echo("deleting.")
                r = state.ld.delete_device(idev[k])
                print("====>",r)


@unprovision.command("rooms")
def unprov_rooms(excel_file, sheet="LD Rooms", interactive:bool=False):
    wb = xlrd.open_workbook(excel_file)
    sh = wb.sheet_by_name(sheet)

    rlist = state.ld.get_rooms()
    rkeys = { r["label"]: r["room_key"] for r in rlist }
    for rowx in range(1, sh.nrows):
        label = sh.cell_value(rowx, 0)
        if label in rkeys:
            typer.echo("Deleting %s" % (label))
            if interactive:
                r = input("ok?")
                if r.lower() not in ["y","yes"]:
                    continue
                typer.echo("deleting.")
            r = state.ld.delete_room(rkeys[label])
            print("====>",r)


### MAIN ###

app = typer.Typer()
app.add_typer(show, name="show")
app.add_typer(add, name="add")
app.add_typer(delete, name="delete")
app.add_typer(provision, name="provision")
app.add_typer(unprovision, name="unprovision")

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
