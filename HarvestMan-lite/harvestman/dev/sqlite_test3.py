import sqlite3
import datetime, time

def adapt_datetime(ts):
    return time.mktime(ts.timetuple())

sqlite3.register_adapter(datetime.datetime, adapt_datetime)
                         
con = sqlite3.connect("test")
c = con.cursor()

c.execute("drop table if exists projects")
c.execute("create table projects (id integer primary key autoincrement default 0, date real, project text)")
#cur.execute("select ?", (p,))
#print cur.fetchone()[0]
c.execute("insert into projects (date, project) values (?, ?)", (datetime.datetime.now(), 'project1'))
time.sleep(1.0)
c.execute("insert into projects (date, project) values (?, ?)", (datetime.datetime.now(), 'project2'))
time.sleep(1.0)
c.execute("insert into projects (date, project) values (?, ?)", (datetime.datetime.now(), 'project3'))

c.execute("select max(id) from projects")
print c.fetchone()[0]

c.close()


