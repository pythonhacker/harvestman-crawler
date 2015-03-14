# HTTP 403 Error #

Sometimes when you try to crawl a site, you get an error as follows.

```
[2010-01-10 13:18:34,965] Starting project en.wikipedia.org ...
[2010-01-10 13:18:34,965] Writing Project Files... 
[2010-01-10 13:18:35,005] Starting download of url http://en.wikipedia.org/wiki/List_of_airports_by_IATA_code:_A ...
[2010-01-10 13:18:35,095] Reading Project Cache... 
[2010-01-10 13:18:35,100] Downloading http://en.wikipedia.org/wiki/List_of_airports_by_IATA_code:_A
[2010-01-10 13:18:36,015] Forbidden =>  http://en.wikipedia.org/wiki/List_of_airports_by_IATA_code:_A
[2010-01-10 13:18:37,023] Ending Project en.wikipedia.org ...
```

Most of the time this is because the web-site does not accept the
USER-AGENT string of the crawler. To fix this you need to
change the USER-AGENT of HarvestMan to a more acceptable one.

# Work-around #

If using the config XML file then you can cheat the web-site
by supplying a standard browser USER-AGENT. For example,

```
    <system>
      <useragent value="Firefox/v3.5" />
      <workers status="1" size="10" timeout="1200"/>
      <trackers value="10"/>
      <timegap value="3.0" random="1" />
      <connections type="flush" />
    </system>
```

You can also do this directly in code as follows. For example,

```
    spider = HarvestMan()
    spider.initialize()
    config = spider.get_config()
    config.USER_AGENT = "Firefox/v3.5"
```

The basic idea is to use a USER\_AGENT string that is more
popular, such as that of the Firefox web browser. This
works for most of the web-pages and gets rid of the HTTP
403 error.