import zeep
import zeep.transports
import requests
import functools
import urllib.parse

class LifeDomus(object):
    def __init__(self, baseurl, pwd, verify=True):
        self.password = pwd
        sess = requests.Session()
        if not verify:
            sess.verify = False
        t = zeep.transports.Transport(session=sess)
        for svc in ["CoreServices", "State", "Account", "User", "Modularization",
                   "Connector", "Site", "Theme", "Device", "Tydom", "Alert", "Room"]:
            n = svc.lower()
            s = zeep.Client(urllib.parse.urljoin(baseurl,"/DomoBox/"+svc+"?wsdl"), transport=t)
            setattr(self, n, s)
        self.login()
        self.set_site()
    @property
    def skey(self):
        return dict(session_key=self.session_key)
    @property
    def sskey(self):
        return dict(session_key=self.session_key, site_key=self.site)
    def login(self):
        self.session_key = self.account.service.Identify(password=self.password, force=True)

    def logged(f):
        @functools.wraps(f)
        def g(self, *args, **kargs):
            try:
                return f(self, *args, **kargs)
            except zeep.exceptions.Fault:
                self.login()
                return f(self, *args, **kargs)
        return g

    @logged
    def set_site(self, site=None):
        sites=self.site.service.GetList()
        if site is None:
            self.site = sites[0]
        else:
            raise NotImplementedError

    @logged
    def get_domains(self):
        domains = {}
        for domain in self.device.service.GetDomainsObjectList():
            catd = {}
            for cat in self.device.service.GetCategoriesList(domain["domn_clsid"]):
                catdesc = self.device.service.GetCategoryDescriptor(catg_clsid=cat, **self.skey)
                devd = {}
                for dev in self.device.service.GetTypesObjectList(catdesc["catg_clsid"]):
                    devd[dev["devc_clsid"]] = dev
                catd[catdesc["catg_clsid"]] = (catdesc, devd)
            domains[domain["domn_clsid"]] = (domain, catd)
        return domains

    @logged
    def show_connectors(self):
        for c in self.connector.service.GetObjectList(**self.skey):
            print("{0[connector_key]}: {0[catg_clsid]} {0[label]}".format(c))
    @logged
    def get_connectors(self):
        return self.connector.service.GetObjectList(**self.skey)
    @logged
    def get_connector_key(self, label):
        cnl = self.get_connectors()
        for c in cnl:
            if c["label"] == label:
                return c["connector_key"]
        else:
            raise KeyError(label)

    @logged
    def get_rooms(self):
        return self.room.service.GetObjectList(**self.sskey)
    @logged
    def get_room_key(self, label):
        rl = self.get_rooms()
        for r in rl:
            if r["label"] == label:
                return r["room_key"]
        else:
            raise KeyError(label)
    @logged
    def get_room(self, room):
        if not room.startswith("ROOM_"):
            room = self.get_room_key(room)
        return self.room.service.GetRoomDescriptor(room_key=room, **self.sskey)
    @logged
    def get_area(self, room):
        if not room.startswith("ROOM_"):
            room = self.get_room_key(room)
        return self.room.service.GetAreaDescription(room_key=room, **self.sskey)
    @logged
    def set_room_picture(self, room, picture_key):
        if not room.startswith("ROOM_"):
            room = self.get_room_key(room)
        self.room.service.SetPictureKey(room_key=room, picture_key=picture_key, **self.sskey)
    @logged
    def add_room(self, clsid, label):
        return self.room.service.AddRoom(room_item_clsid=clsid, label=label, **self.sskey)
    @logged
    def delete_room(self, room):
        if not room.startswith("ROOM_"):
            room = self.get_room_key(room)
        return self.room.service.DeleteRoom(room_key=room, **self.sskey)

    @logged
    def get_devices(self):
        return self.device.service.GetObjectList(**self.sskey)
    @logged
    def get_device_key(self, label):
        dl = self.get_devices()
        for d in dl:
            if d["label"] == label:
                return d["device_key"]
        else:
            raise KeyError(label)

    @logged
    def delete_device(self, key):
        return self.device.service.DeleteDevice(device_key=key, **self.sskey)
    @logged
    def get_device(self, key):
        return self.device.service.GetDeviceDescriptor(device_key=key, **self.sskey)
    @logged
    def get_device_class_from_label(self, lbl):
        for domain in self.device.service.GetDomainsObjectList():
            for cat in self.device.service.GetCategoriesList(domain["domn_clsid"]):
                catdesc = self.device.service.GetCategoryDescriptor(catg_clsid=cat, **self.skey)
                for dev in self.device.service.GetTypesObjectList(catdesc["catg_clsid"]):
                    if ("{%s}" % lbl) == dev["label"]:
                        return dev["devc_clsid"]
        raise KeyError(lbl)

    @logged
    def get_device_properties(self, key):
        return self.device.service.GetPropertiesObjectList(device_key=key, **self.sskey)
    @logged
    def set_device_picture(self, dev, picture_key):
        self.device.service.SetPictureKey(device_key=dev, picture_key=picture_key,
                                             **self.sskey)
    @logged
    def add_device(self, clsid, label, room, connector):
        room_key = self.get_room_key(room)
        connector_key = self.get_connector_key(connector)
        dev = self.device.service.AddDevice(device_clsid=clsid, label=label, **self.sskey)
        if not self.device.service.SetConnector(device_key=dev, connector_key=connector_key, **self.sskey):
            raise Exception
        if not self.device.service.SetRoom(device_key=dev, room_key=room_key, **self.sskey):
            raise Exception
        return dev
    @logged
    def set_device_property_ctrl(self, dev, prop, ref):
        self.device.service.SetPropertyRefCtrl(device_key=dev, prop_clsid=prop,
                                               prop_numr=0, refr_ctrl=ref, **self.sskey)
    @logged
    def set_device_property_indc(self, dev, prop, ref):
        self.device.service.SetPropertyRefIndc(device_key=dev, prop_clsid=prop,
                                               prop_numr=0, refr_indc=ref, **self.sskey)
    @logged
    def add_knx_light(self, label, room, knx_grp_write, knx_grp_read):
        dev = self.add_device("CLSID-DEVC-A-EC01", label, room, "KNX IP")
        self.device.service.SetPropertyRefCtrl(device_key=dev, prop_clsid="CLSID-DEVC-PROP-TOR-SW",
                                               prop_numr=0, refr_ctrl=knx_grp_write, **self.sskey)
        self.device.service.SetPropertyRefIndc(device_key=dev, prop_clsid="CLSID-DEVC-PROP-TOR-SW",
                                               prop_numr=0, refr_indc=knx_grp_read, **self.sskey)
        return dev

    @logged
    def add_knx_dimmer(self, label, room, cmd_write, cmd_read, val_write, val_read):
        dev = self.add_device("CLSID-DEVC-A-EC03", label, room, "KNX IP")
        self.device.service.SetPropertyRefCtrl(device_key=dev, prop_clsid="CLSID-DEVC-PROP-DIMMER-SW",
                                               prop_numr=0, refr_ctrl=cmd_write, **self.sskey)
        self.device.service.SetPropertyRefIndc(device_key=dev, prop_clsid="CLSID-DEVC-PROP-DIMMER-SW",
                                               prop_numr=0, refr_indc=cmd_read, **self.sskey)
        self.device.service.SetPropertyRefCtrl(device_key=dev, prop_clsid="CLSID-DEVC-PROP-DIMMER-VA-POS",
                                               prop_numr=0, refr_ctrl=val_write, **self.sskey)
        self.device.service.SetPropertyRefIndc(device_key=dev, prop_clsid="CLSID-DEVC-PROP-DIMMER-VA-POS",
                                               prop_numr=0, refr_indc=val_read, **self.sskey)
        return dev
