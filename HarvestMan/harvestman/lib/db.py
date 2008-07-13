# -- coding: utf-8
"""
db.py - Provides HarvestManDbManager class which takes care
of creating and managing the user's crawl database. The
crawl database is an sqlite database created as
$HOME/.harvestman/db/crawls.db where $HOME is the home
directory of the user. The crawls database is updated with
meta-data of every crawl after a crawl is completed.

Created by Anand B Pillai <abpillai at gmail dot com> Mar 26 2008

Copyright (C) 2008 Anand B Pillai.

"""

import os, sys
import time

from common.common import objects, extrainfo, logconsole

def adapt_datetime(ts):
    return time.mktime(ts.timetuple())

class HarvestManDbManager(object):
    """ Class performing the creation/management of crawl databases """

    projid = 0

    @classmethod
    def try_import(cls):
        try:
            import sqlite3
            return sqlite3
        except ImportError, e:
            pass
            
    @classmethod
    def create_user_database(cls):

        sqlite3 = cls.try_import()
            
        if sqlite3 is None:
            return

        logconsole("Creating user's crawl database file in %s..." % objects.config.userdbdir)
        
        dbfile = os.path.join(objects.config.userdbdir, "crawls.db")
        conn = sqlite3.connect(dbfile)
        c = conn.cursor()
        
        # Create table for projects
        c.execute("drop table if exists projects")
        c.execute("""create table projects (id integer primary key autoincrement default 0, time real, name text, url str, config str)""")
        # Create table for project statistics
        # We are storing the information for
        # 1. number of urls scanned
        # 2. number of urls processed (fetched/crawled)
        # 3. number of URLs which were crawl-filtered
        # 4. number of urls failed to fetch
        # 5. number of urls with 404 errors
        # 6. number of URLs which hit the cache
        # 7. number of servers scanned
        # 8. number of unique directories scanned
        # 9. number of files saved
        # 10. Amount of data fetched in bytes
        # 11. the total time for the crawl.
        c.execute("drop table if exists project_stats")        
        c.execute("""create table project_stats (project_id integer primary key, urls integer, procurls integer, filteredurls integer, failedurls integer, brokenurls integer, cacheurls integer, servers integer, directories integer, files integer, data real, duration text)""")
        
        c.close()

    @classmethod
    def add_project_record(cls):

        sqlite3 = cls.try_import()
        if sqlite3 is None:
            return
        
        extrainfo('Writing project record to crawls database...')
        dbfile = os.path.join(objects.config.userdbdir, "crawls.db")
        
        # Get the configuration as a pickled string
        cfg = objects.config.copy()

        conn = sqlite3.connect(dbfile)
        c = conn.cursor()
        c.execute("insert into projects (time, name, url, config) values(?,?,?,?)",
                  (time.time(),cfg.project,cfg.url, repr(cfg)))
        conn.commit()

        # Fetch the most recent project id and save it as projid
        c.execute("select max(id) from projects")
        cls.projid = c.fetchone()[0]
        # print 'project id=>',cls.projid
        c.close()
        extrainfo("Done.")

    @classmethod
    def add_stats_record(cls, statsd):

        sqlite3 = cls.try_import()        
        if sqlite3 is None:
            return

        logconsole('Writing project statistics to crawl database...')
        dbfile = os.path.join(objects.config.userdbdir, "crawls.db")
        conn = sqlite3.connect(dbfile)
        c = conn.cursor()
        t = (cls.projid,
             statsd['links'],
             statsd['processed'],
             statsd['filtered'],
             statsd['fatal'],
             statsd['broken'],
             statsd['filesinrepos'],
             statsd['extservers'] + 1,
             statsd['extdirs'] + 1,
             statsd['files'],
             statsd['bytes'],
             '%.2f' % statsd['fetchtime'])
             
        c.execute("insert into project_stats values(?,?,?,?,?,?,?,?,?,?,?,?)", t)
        conn.commit()
        c.close()
        pass

if __name__ == "__main__":
    HarvestManDbManager.create_user_database()
    pass

