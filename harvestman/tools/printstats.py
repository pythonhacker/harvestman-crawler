"""
printstats.py - Print project statistics and information
by reading the user's crawls database.

Created by Anand B Pillai <abpillai at gmail dot com> May 30 2008

Copyright (C) 2008 Anand B Pillai.
"""
import sys
import os
import time

try:
    import sqlite3
except ImportError:
    sys.exit('sqlite3 module not found!')

conn = sqlite3.connect(os.path.expanduser("~/.harvestman/db/crawls.db"))
c1 = conn.cursor()
cur = c1.execute("select *  from projects order by id")

for member in c1:
    # project id is first member
    proj_id = member[0]
    print 'Project #%d crawled at [%s] with URL {%s}, saved to name "<%s>"...' % (proj_id, time.ctime(float(member[1])),
                                                                     member[3], member[2])
    c2 = conn.cursor()
    c2.execute("select * from project_stats where project_id=%d" % proj_id)
    data = c2.fetchall()
    if len(data)==0: continue

    data = data[0]
    print 'Statistics'
    print '----------'
    print '  Total # of URLs=>',data[1]
    print '  Processed URLs=>',data[2]
    print '  Filtered URLs=>',data[3]
    print '  Failed URLs=>',data[4]
    print '  Broken URLs=>',data[5]
    print '  URLs found in Cache=>',data[6]
    print '  # of domains=>',data[7]
    print '  # of directories=>',data[8]
    print '  # of files=>',data[9]
    print '  Data downloaded=>',data[10],'bytes.'
    print '  Duration=>',data[11],'seconds.'
    c2.close()

c1.close()
conn.close()
