import sqlite3
import datetime, time

def adapt_datetime(ts):
    return time.mktime(ts.timetuple())

sqlite3.register_adapter(datetime.datetime, adapt_datetime)
                         
con = sqlite3.connect("/home/anand/.harvestman/db/crawls.db")
c = con.cursor()

c.execute("select * from project_stats")
print c.fetchall()

c.close()


