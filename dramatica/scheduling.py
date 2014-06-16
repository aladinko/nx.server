#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from .common import DramaticaObject, DramaticaAsset
from .timeutils import *

DEFAULT_BLOCK_DURATION = 600

class DramaticaBlock(DramaticaObject):
    default = {}
    def __init__(self, rundown, **kwargs):
        super(DramaticaBlock, self).__init__(**kwargs)
        self.rundown = rundown
        self.cache = rundown.cache
        self.items = []
        self.config = {} # solver settings (event "dramatica/config" meta)
        self.solved = False

    @property
    def block_order(self):
        for i, b in enumerate(self.rundown.blocks):
            if b == self:
                return i

    @property 
    def target_duration(self):
        return self["target_duration"] or self.scheduled_end - self.broadcast_start

    @property
    def duration(self):
        dur = 0
        for item in self.items:
            dur += item.duration
        return dur
        
    @property 
    def remaining(self):
        return self.target_duration - self.duration

    @property
    def scheduled_start(self):
        return self["start"] or self.broadcast_start

    @property
    def scheduled_end(self):
        try:
            return self.rundown.blocks[self.block_order+1].scheduled_start
        except IndexError:
            return self.rundown.day_start + (3600*24)

    @property
    def broadcast_start(self):
        if self.block_order == 0:
            return self.scheduled_start
            #return self.rundown.day_start
        return self.rundown.blocks[self.block_order-1].broadcast_end

    @property 
    def broadcast_end(self):
        if self.solved and self.items:
            return self.broadcast_start + self.duration
        else:
            return self.scheduled_end
            
    def add(self, item, **kwargs):
        if not item:
            return
        if type(item) == int and item in self.cache.assets:
            self.items.append(self.cache[item])
            return
        assert type(item) == DramaticaAsset
        self.items.append(item)
        self.items[-1].meta.update(kwargs)

    def solve(self):

        #TODO: Loading solvers
        from .solving import DefaultSolver, MusicBlockSolver
        if self.config.get("solver", False) == "MusicBlock":
            solver_class = MusicBlockSolver
        else:
            solver_class = DefaultSolver

        self.config["genres"] = self.config.get("genres", [])
            .extend([item["genre/music"] in item in self.items if item["genre/music"] ])
            .extend([item["genre/movie"] in item in self.items if item["genre/movie"] ])

        solver = solver_class(self)
        solver.solve()

        self.solved = True










class DramaticaRundown(DramaticaObject):
    default = {
        "day"        : today(),
        "id_channel" : 1,
        "day_start"  : (6,00)
    }

    def __init__(self, cache, **kwargs):
        super(DramaticaRundown, self).__init__(**kwargs)
        self.block_types = {}
        self.blocks = []
        self.cache = cache

    def clock(self, hh, mm):
        """Converts hour and minute of current day to unix timestamp"""
        ttuple = list(self["day"]) + [hh, mm]
        dt = datetime.datetime(*ttuple)
        tstamp = time.mktime(dt.timetuple())  
        if tstamp < self.day_start:
            tstamp += 3600*24
        return tstamp

    @property
    def dow(self):
        return datetime.datetime(*self["day"]).weekday()

    @property
    def day_start(self):
        ttuple = list(self["day"]) + list(self["day_start"])
        dt = datetime.datetime(*ttuple)
        return time.mktime(dt.timetuple())  

    @property 
    def day_end(self):
        return self.day_start + (24*3600)

    def add(self, block):
        assert type(block) == DramaticaBlock
        self.blocks.append(block)

    def __str__(self):
        output = u"\n"
        for block in self.blocks:
            output += u"{}  {}   {}\n".format(
                unicode(time.strftime("%H:%M", time.localtime(block.scheduled_start))),
                unicode(time.strftime("%H:%M", time.localtime(block.broadcast_start))),
                block["title"]
                )
            output += u"-"*64 + "\n"

            for item in block.items:
                output+=u"             {} {}\n".format(
                        u" " if item["dramatica/auto"] else u"*",
                        unicode(item["title"])
                    )
            output += u"\n\n"


        return output