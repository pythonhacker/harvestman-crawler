import sqlite3
import datetime, time

def adapt_datetime(ts):
    return time.mktime(ts.timetuple())

sqlite3.register_adapter(datetime.datetime, adapt_datetime)
                         
con = sqlite3.connect("test")
c = con.cursor()

now = datetime.datetime.now()
c.execute("drop table if exists times")
c.execute("create table times (time real)")
#cur.execute("select ?", (p,))
#print cur.fetchone()[0]
c.execute("insert into times values (?)", (now,))

c.execute("select * from times")
print c.fetchall()

c.close()


