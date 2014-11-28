#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

NX_ROOT = os.path.abspath(os.path.split(sys.argv[0])[0])

if not NX_ROOT in sys.path:
    sys.path.append(NX_ROOT)

if NX_ROOT != os.getcwd():
    os.chdir(NX_ROOT)


import subprocess
import thread

from optparse import OptionParser

from nx import *
from nx.shell import shell



class StorageMonitor():
    def __init__(self,once=False):
        if once: 
            self._main()
        else:    
            thread.start_new_thread(self._run,())
            logging.info("Storage monitor started")

    def _run(self):
        while True:
            self._main()
            time.sleep(60)

    def _main(self):
        for id_storage in storages:
            storage = storages[id_storage]
            if ismount(storage.get_path()): 
                storage_string = "{}:{}".format(config["site_name"], storage.id_storage)
                storage_ident_path = os.path.join(storage.get_path(),".nebula_root")
                
                if not (os.path.exists(storage_ident_path) and storage_string in [line.strip() for line in open(storage_ident_path).readlines()]):
                    try:
                        f = open(storage_ident_path, "a")
                        f.write(storage_string+"\n")
                        f.close()
                    except: 
                        pass
                continue

            logging.info ("Storage %s (%s) is not mounted. Remounting."%(storage.id_storage,storage.title))

            if not os.path.exists(storage.get_path()):
                try:     
                    os.mkdir(storage.get_path())
                except:  
                    logging.error("Unable to create mountpoint for storage %s (%s)"%(storage.id_storage,storage.title))   
                    continue
            
            self.mount(storage.protocol, storage.path, storage.get_path(), storage.login, storage.password)
            
            if ismount(storage.get_path()):     
                logging.goodnews("Storage %s (%s) remounted successfully"%(storage.id_storage,storage.title))
            else:                     
                logging.warning ("Storage %s (%s) remounting failed"%(storage.id_storage,storage.title)) 


    def mount(self, protocol, source, destination, username="", password=""):
        if protocol == CIFS:
         
            if username and password:
                credentials = ",username="+username+",password="+password
            else:
                credentials = ""
         
            host = source.split("/")[2]
            cmd = "mount -t cifs %s %s -o 'rw, iocharset=utf8, file_mode=0666, dir_mode=0777%s'" % (source,destination,credentials)

        elif protocol == NFS:
            cmd = "mount -t nfs %s %s"%(source,destination) 
         
        elif protocol == FTP:
            cmd = "curlftpfs -o umask=0777,allow_other,direct_io %s:%s@%s %s"%(username,password,source,destination)
            
        else:
            return  

        c = shell(cmd) 
        print c.stderr().read()






class ServiceMonitor():
    def __init__(self):
        self.services = {}
        db = DB()
        db.query("SELECT id_service,pid FROM nx_services WHERE host='%s'" % HOSTNAME)
        for id_service, pid in db.fetchall(): 
            if pid:
                self.kill_service(r[1])
        db.query("UPDATE nx_services SET state = 0 WHERE host='%s'" % HOSTNAME)
        db.commit()

        thread.start_new_thread(self._run,())
        logging.info("Service monitor started")
        
    def get_running_services(self):
        result = []
        for id_service in self.services.keys():
            proc, title = self.services[id_service]
            if proc.poll() == None:
                result.append((id_service, title))
        return result

    def _run(self):
        while True:
            self._main()
            time.sleep(1)

    def _main(self):
        db = DB()
        db.query("SELECT id_service, agent, title, autostart, loop_delay, settings, state, pid FROM nx_services WHERE host='%s'" % HOSTNAME)
     
        for id_service, agent, title, autostart, loop_delay, settings, state, pid in db.fetchall():
            if state == STARTING: # Start service
                if not id_service in self.services.keys():
                    self.start_service(id_service, title, db = db)

            elif state == KILL: # Kill service
                if id_service in self.services.keys():
                    self.kill_service(self.services[id_service][0].pid)

        ## Starting / Stopping
        #######################
        ## Real state

        for id_service in self.services.keys():
            proc, title = self.services[id_service]
            if proc.poll() == None: continue
            del self.services[id_service]
            logging.warning("Service %s (%d) terminated"%(title,id_service))
            db.query("UPDATE nx_services SET state = 0  WHERE id_service = %d"%(id_service))
            db.commit()
          
        ## Real state
        ########################
        ## Autostart
          
        db.query("SELECT id_service, title, state, autostart FROM nx_services WHERE host = '%s' AND state=0 AND autostart=1" % HOSTNAME)
        for id_service, title, state, autostart in db.fetchall():
            if not id_service in self.services.keys():
                logging.debug("AutoStarting service %s (%s)"% (title, id_service))
                self.start_service(id_service, title)
            
    def start_service(self, id_service, title, db=False):
        proc_cmd = [
            python_cmd, 
            os.path.join(NX_ROOT, "run_service.py"), 
            str(id_service), 
            "\"{}\"".format(title)
            ]

        logging.info("Starting service {} - {}".format(id_service, title))

        self.services[id_service] = [
            subprocess.Popen(proc_cmd, cwd=NX_ROOT), 
            title
            ]
        # PID & Heartbeat should be updated by run_service py
    

    def stop_service(self, id_service, title, db=False):
        logging.info("Stopping service %d - %s"%(id_service, title))
        #well... service should stop itself :-/


    def kill_service(self, pid=False, id_service=False):    
        if id_service in self.services:
            pid = self.services[id_service][0].pid
        if pid == os.getpid() or pid == 0: 
            return
        logging.info("Attempting to kill PID {}".format(pid))
        if PLATFORM == "linux":
            os.system (os.path.join(NX_ROOT,"killgroup.sh {}".format(pid)))
        elif PLATFORM == "windows":
            os.system ("taskkill /F /PID %s" % pid)




def nebula_run():    
    storage_monitor = StorageMonitor()
    service_monitor = ServiceMonitor()

    logging.debug("Starting admin interface")
    admin = subprocess.Popen([os.path.join("admin", "run_admin.py"), format(NX_ROOT)], cwd=NX_ROOT)

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt):
        services = service_monitor.services.keys()
        for id_service in services:
            service_monitor.kill_service(id_service=id_service)





if __name__ == "__main__":
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage)

    parser.add_option("-d", "--daemon", dest="daemon",
                          help="Control Nebula in daemon mode: start, stop, restart", 
                          action="store",
                          type="string",
                          )

    (options, args) = parser.parse_args()



    if options.daemon:

        from daemon import NebulaDaemon
        
        daemon = NebulaDaemon(proc=nebula_run, root=NX_ROOT)

        if options.daemon == 'start':
            daemon.start()
        elif options.daemon == 'stop':
            daemon.stop()
        elif options.daemon == 'restart':
            daemon.restart()
        else:
            sys.stderr.write("Unknown daemon control command. Should be: start / stop / restart\n")
            sys.exit(2)

        sys.exit(0)

    else:
        nebula_run()