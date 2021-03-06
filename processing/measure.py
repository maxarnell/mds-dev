"""
Helper python script that contains code to construct and measure average number of 
bikes available in a given area. 

Author: David Klinger
"""

import argparse
import sqlalchemy
import psycopg2
import pandas
import fiona
import pyproj
import shapely.geometry
import shapely.ops
import shapely.wkt
import pprint
import time
import datetime
import sortedcontainers

# class to hold information on intervals, as keys
class interval:

    # specification: one interval holds a start and end time
    # in seconds, unix std time
    def __init__(self,start,end):
        self.start = start
        self.end = end

    # comparison ops only defined on start time
    # to avoid weird behavior with bisect_right
    def __lt__(self,interval):
        return self.start < interval.start

    def __eq__(self, interval):
        return self.start == interval.start

    def __str__(self):
        return "({}, {})".format(self.start,self.end)

    def __repr__(self):
        return "({}, {})".format(self.start,self.end)

    def __hash__(self):
        return hash(self.__repr__())

# class to hold and edit intervals of time
# each interval maps to a # of vehicles available
class intervals:

    def __init__(self,start,end):
        self.counts = sortedcontainers.SortedDict()
        i = interval(int(start),int(end))
        self.counts[i] = 0

    def add_interval(self,t_s,t_e):
        i = self.counts.bisect_right(interval(t_s,t_e))-1
        if i<0:
            i = 0
        to_remove = sortedcontainers.SortedSet()
        to_add = sortedcontainers.SortedDict()
        while i < len(self.counts) and (self.counts.keys()[i].start < t_e or t_e is None):
            key = self.counts.keys()[i]
            s = key.start
            e = key.end
            cnt = self.counts[key]
            if t_e is not None:
                if t_s <= s and t_e >= e:
                    to_add[interval(s,e)] = cnt+1
                elif t_s <= s and t_e > s and t_e < e:
                    to_remove.add(key)
                    to_add[interval(s,t_e)] = cnt+1
                    to_add[interval(t_e,e)] = cnt
                elif t_s > s and t_s < e and t_e >= e:
                    to_remove.add(key)
                    to_add[interval(s,t_s)] = cnt
                    to_add[interval(t_s,e)] = cnt+1
                elif t_s > s and t_e < e:
                    to_remove.add(key)
                    to_add[interval(s,t_s)] = cnt
                    to_add[interval(t_s,t_e)] = cnt+1
                    to_add[interval(t_e,e)] = cnt
            else:
                if t_s <= s:
                    to_add[interval(s,e)] = cnt+1
                elif t_s > s:
                    to_remove.add(key)
                    to_add[interval(s,t_s)] = cnt
                    to_add[interval(t_s,e)] = cnt+1
            i += 1

        for r in to_remove:
            self.counts.pop(r)
        for k in to_add.keys():
            self.counts[k] = to_add[k]


def measure(db, start, end, area, debug=True):
    i_s = intervals(start,end)
    if debug:
        print("Now analyzing {} intervals.".format(len(db)))
    for i,r in db.iterrows():
        if i%500==0 and debug:
            print("{} of {}".format(i,len(db)))
        t_s = r['start_time']
        t_e = r['end_time']
        loc = r['location']
        loc = shapely.wkt.loads(loc)
        # loc = shapely.geometry.Point(float(loc[0]), float(loc[1]))
        if area.contains(loc):
            i_s.add_interval(t_s,t_e)
    s = 0
    for k in i_s.counts.keys():
        if k in i_s.counts.keys():
            # sometimes value is removed but not the key itself with pop
            # bug in library?
            s += i_s.counts[k]*(k.end-k.start)
    if debug:
        print("done.")
    return s/(end-start)
