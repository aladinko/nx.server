#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from nx.common import *

from default_db import *
from default_meta import *


## key, value
SITE_SETTINGS = [
    ("seismic_addr" , "224.168.2.8"),
    ("seismic_port" , "42112"),
    ("cache_driver" , "null"),
    ("cache_host"   , "192.168.32.320"),
    ("cache_port"   , "11211")
]


## id_folder, title, color
FOLDERS = [
(1, "Music videos", 0xe34931),
(2, "Movies"      , 0x019875),
(3, "Jingles"     , 0xeec050)
]


## agent, title, host, autostart, loop_delay, settings
SERVICES = [
("watch", "Watch", HOSTNAME, 1, 20,"""<settings><mirror><storage>1</storage><path>Jingles</path><recursive>0</recursive><meta tag='variant'>Library</meta><post>asset["id_folder"] = 3</post></mirror></settings>"""),
("meta" , "Meta" , HOSTNAME, 1, 20,"""<settings></settings>""")
]


## id_storage, title, protocol, path, login, password
STORAGES = [
(1, "Test", LOCAL, "c:\\martas\\opennx\\", "", "")
]






##############################################################
## create db structure

if os.path.exists(config["db_host"]):
    try:    os.remove(config["db_host"])
    except: critical_error("Unable to remove old DB File")

db = DB()
for q in SQLITE_TPL:
    db.query(q)
db.commit()

## create db structure
##############################################################
## metadata set

for ns, tag, editable, searchable, class_, settings in BASE_META_SET:
    print "%s/%s"%(ns,tag)
    q = """INSERT INTO nx_meta_types (namespace, tag, editable, searchable, class, settings) VALUES('%s' ,'%s', %d, %d, %d, '%s')""" % \
           (ns, tag, editable, searchable, class_, json.dumps(settings))
    db.query(q)
db.commit()

## metadata set
##############################################################
## site settings

for key, value in SITE_SETTINGS:
    q = """INSERT INTO nx_settings(key,value) VALUES ('%s','%s')""" % (key, value)
    db.query(q)
db.commit()

## site settings
##############################################################
## folders

for id_folder, title, color in FOLDERS:
  q = "INSERT INTO nx_folders (id_folder, title, color) VALUES (%d,'%s',%d)" % (id_folder, title, color)
  db.query(q)
db.commit()

## folders
##############################################################
## services

for agent, title, host, autostart, loop_delay, settings in SERVICES:
    q = "INSERT INTO nx_services (agent, title, host, autostart, loop_delay, settings, state, pid, last_seen) VALUES ('%s','%s','%s',%d, %d, '%s',0,0,0)" % \
        (agent, title, host, autostart, loop_delay, db.sanit(settings))
    db.query(q)
db.commit()

## services
##############################################################
## storages

for id_storage, title, protocol, path, login, password in STORAGES:
    q = "INSERT INTO nx_storages (id_storage, title, protocol, path, login, password) VALUES (%d, '%s', %d, '%s', '%s', '%s')" % \
        (id_storage, db.sanit(title), protocol, db.sanit(path), db.sanit(login), db.sanit(password))

db.commit() 