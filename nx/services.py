#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *

class ServicePrototype(object):
    def __init__(self, id_service, settings=False):
        logging.info("Initialising service")
        self.id_service = id_service
        self.settings   = settings
        self.onInit()
        logging.goodnews("Service started")

    def onInit(self):
        pass

    def onMain(self):
        pass        

    def heartBeat(self):
        db = DB()
        db.query("SELECT state FROM nx_services WHERE id_service=%s" % self.id_service)
        try:
            state = db.fetchall()[0][0]
        except:
            state = KILL
        else:
            db.query("UPDATE nx_services SET last_seen = %d, state=1 WHERE id_service=%d" % (time(), self.id_service))

        if state in [STOPPED, STOPPING, KILL]:
            logging.info("Shutting down")
            sys.exit(1)

__all__ = ["ServicePrototype"]