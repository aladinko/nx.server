#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
from nx.objects import Asset
from nx.common.metadata import meta_types

from probes import probes


class Service(ServicePrototype):
    def on_init(self):
        filters = []
        #filters.append("status=%d"%CREATING)
        if filters:
            self.filters = "AND " + " AND ".join(filters)
        else: 
            self.filters = ""

    def on_main(self):
        self.mounted_storages = []
        for id_storage in storages:
            sp = storages[id_storage].get_path()
            if os.path.exists(sp) and len(os.listdir(sp)) != 0:
                self.mounted_storages.append(id_storage)

        db = DB()
        db.query("SELECT id_object FROM nx_assets {} WHERE media_type=0".format(self.filters))
        for id_asset, in db.fetchall():
            self._proc(id_asset, db)

    def _proc(self, id_asset, db):
        asset = Asset(id_asset, db = db)
        fname = asset.get_file_path()

        if asset["id_storage"] not in self.mounted_storages:
            return

        if not os.path.exists(fname):
            if asset["status"] == ONLINE:
                logging.warning("Turning offline %s" % asset)
                asset["status"] = OFFLINE
                print "sav"
                asset.save()
                print (asset["status"])
            return

        try:
            fmtime = int(os.path.getmtime(fname))
            fsize  = int(os.path.getsize(fname))
        except:
            self.logging.error("Strange error 0x001 on %s" % asset)
            return

        if fsize == 0: 
            return

        if fmtime != asset["file/mtime"] or asset["status"] == RESET:
            try:    
                f = open(fname,"rb")
            except: 
                logging.debug("File creation in progress. %s" % asset)
                return
            else:
                f.seek(0,2)
                fsize = f.tell()
                f.close()
            
            # Filesize must be changed to update metadata automatically. 
            # It sucks, but mtime only condition is.... errr doesn't work always
            
            if fsize == asset["file/size"] and asset["status"] != RESET:
                asset["file/mtime"] = fmtime
                asset.save(set_mtime=False)
            else:
                logging.info("Updating metadata %s" % asset)

                keys = list(asset.meta.keys())
                for key in keys:
                    if meta_types[key].namespace in ("fmt", "qc"):
                        del (asset.meta[key])

                asset["file/size"]  = fsize
                asset["file/mtime"] = fmtime
            
                #########################################
                ## PROBE

                for probe in probes:
                    if probe.accepts(asset):
                        logging.debug("Probing %s using %s" % (asset, probe))
                        asset = probe.work(asset)

                ## PROBE
                #########################################

                if asset["status"] == RESET:
                    asset["status"] = ONLINE
                    logging.info("%s reset completed" % asset)
                else:
                    asset["status"] = CREATING
                asset.save()
        
   
        if asset["status"] == CREATING and asset["mtime"] + 15 > time.time(): 
            logging.debug("Waiting for %s completion assurance." % asset)
            asset.save(set_mtime=False)

        elif asset["status"] in (CREATING, OFFLINE):
            logging.goodnews("Turning online %s" % asset)
            asset["status"] = ONLINE
            asset.save()
    
            #db = dbconn()
            #db.query("UPDATE nebula_asset_states SET progress=0, id_service=0 WHERE id_asset=%s AND id_state > 0 and progress = -1" % id_asset)
            #db.commit()       