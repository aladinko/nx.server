#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import thread


from urllib2 import urlopen

from nx import *


class Service(ServicePrototype):
    def on_init(self):

        self.site_name = config["site_name"]

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0",int(config["seismic_port"])))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        status = self.sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,socket.inet_aton(config["seismic_addr"]) + socket.inet_aton("0.0.0.0"));
        self.sock.settimeout(1)

        host = "192.168.32.148"
        port = 11000
        ssl  = True

        self.url = "{protocol}://{host}:{port}/msg_publish?id={site_name}".format(protocol=["http","https"][ssl], host=host, port=port, site_name=config["site_name"])

        thread.start_new_thread(self.listen, ())


    def listen(self):
        while True:
            try:
                message, addr = self.sock.recvfrom(1024)
            except (socket.error):
                continue

            try:
                tstamp, site_name, host, method, data = json.loads(message)
            except:
                logging.warning("Malformed seismic message detected: {}".format(message))
                continue

            if site_name == config["site_name"]:
                self.send_message("{}\n".format(message.replace("\n","")))

    
    def send_message(self, message):
        post_data = message
        result = urlopen(self.url, post_data.encode("ascii"), timeout=1)
        
