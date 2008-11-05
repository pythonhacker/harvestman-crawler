import sqlite3

class Point(object):

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __conform__(self, protocol):
        if protocol is sqlite3.PrepareProtocol:
            return '%f;%f' % (self.x, self.y)

con = sqlite3.connect("test")
c = con.cursor()

p = Point(5.0, 3.5)

c.execute("drop table points")
c.execute("create table points (point text)")
#cur.execute("select ?", (p,))
#print cur.fetchone()[0]
c.execute("insert into points values (?)", (p,))

c.execute("select * from points")
print c.fetchall()

c.close()


