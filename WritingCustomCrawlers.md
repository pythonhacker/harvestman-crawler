# How to use HarvestMan events API to write custom crawlers #

## HarvestMan events API ##
HarvestMan provides a very well-defined events API which can be used by developers to write custom crawlers suited for a specific crawling/data mining task.

### Events ###
Events are implemented using a callback mechanism. At different times during the program execution, HarvestMan raises events with specific names. These events can be hooked into custom functions by subscribing to the events and defining functions which process the state supplied along with the event.

Events are mainly of two types - _post_ events are those that are raised after an action is performed and _pre_ (_before_) events are those that are raised prior to performing an action. In HarvestMan, _pre_ events are more useful for controlling program flow since their return values are checked for True/False to decide rest of processing. Fore more information, read on.

## Illustration ##
Let us say that you want to write a custom crawler which saves only images which are larger than 4K to the disk (a practical example of this would be a crawler which ignores thumbnail images, since thumbnails are typically  of size 2K-4K). This is how you would do this by subscribing to the **_save\_url\_data_** event.

First you need to define a custom crawler class over-riding the _HarvestMan_ class.

```
from harvestman.apps.spider import HarvestMan
from harvestman.lib.common.macros import *

class MyCustomCrawler(HarvestMan):
    """ A custom crawler """

    size_threshold = 4096

    def save_this_url(self, event, *args, **kwargs):
        """ Custom callback function which modifies behaviour
            of saving URLs to disk """

        # Get the url object
        url = event.url
        # If not image, save always
        if not url.is_image():
            return True
        else:
            # If image, check for content-length > 4K
            size = url.clength
            return (size>self.size_threshold)

# Set up the custom crawler
if __name__ == "__main__":
    crawler = MyCustomCrawler()
    crawler.initialize()
    # Get the configuration object
    config = crawler.get_config()
    # Register for 'save_url_data' event which will be called
    # back just before a URL is saved to disk
    crawler.register('save_url_data', crawler.save_this_url)
    # Run
    crawler.main()
```

You can run the program as if you would run HarvestMan. For example if you save this code to a file named _customcrawler.py_ then you would run it as,

```
$ python customcrawler.py [URL]
```

Here is a sample crawl of a site containing images.
```
$ python customcrawler.py http://www.tcm.phy.cam.ac.uk/~pdh1001/Photo_Album/Kilimanjaro/pic0001.html
/usr/local/lib/python2.6/dist-packages/HarvestMan-2.0.4betadev_r210-py2.6.egg/harvestman/lib/crawler.py:53: DeprecationWarning: the sha module is deprecated; use the hashlib module instead
  import sha
/usr/local/lib/python2.6/dist-packages/HarvestMan-2.0.4betadev_r210-py2.6.egg/harvestman/lib/urlparser.py:50: DeprecationWarning: the md5 module is deprecated; use hashlib instead
  import md5
Loading user configuration... 
Starting HarvestMan 2.0 beta 5... 
Copyright (C) 2004, Anand B Pillai 
  
[2010-02-10 19:21:51,052] *** Log Started ***
 
[2010-02-10 19:21:51,052] Starting project www.tcm.phy.cam.ac.uk ...
[2010-02-10 19:21:51,052] Writing Project Files... 
[2010-02-10 19:21:51,191] Starting download of url http://www.tcm.phy.cam.ac.uk/~pdh1001/Photo_Album/Kilimanjaro/pic0001.html ...
[2010-02-10 19:21:51,250] Reading Project Cache... 
[2010-02-10 19:21:51,253] Project cache not found 
[2010-02-10 19:21:51,256] Downloading http://www.tcm.phy.cam.ac.uk/~pdh1001/Photo_Album/Kilimanjaro/pic0001.html
[2010-02-10 19:21:52,211] Saved /home/anand/work/harvestman/HarvestMan-lite/harvestman/apps/samples/www.tcm.phy.cam.ac.uk/www.tcm.phy.cam.ac.uk/~pdh1001/Photo_Album/Kilimanjaro/pic0001.html
[2010-02-10 19:21:52,299] Fetching links http://www.tcm.phy.cam.ac.uk/~pdh1001/Photo_Album/Kilimanjaro/pic0001.html
[2010-02-10 19:21:52,730] Downloading http://www.tcm.phy.cam.ac.uk/~pdh1001/Photo_Album/Kilimanjaro/index.html
[2010-02-10 19:21:52,731] Downloading http://www.tcm.phy.cam.ac.uk/~pdh1001/Photo_Album/Kilimanjaro/pic0002.html
...
```

## Diving deep ##
Let us dissect the custom crawler application we have built to understand the
events API.

Here are the steps involved.

  * Create a custom crawler class inheriting the _HarvestMan_ class.
  * Create a custom function which hooks into a specific event.
  * In the `__main__` section, configure the crawler to subscribe to the event by using the _register_ method. This method takes the event name as first argument and event handler as the second argument.

Let us take a deeper look at the function _save\_this\_url_.

```
    def save_this_url(self, event, *args, **kwargs):
        """ Custom callback function which modifies behaviour
            of saving URLs to disk """

        # Get the url object
        url = event.url
        # If not image, save always
        if not url.is_image():
            return True
        else:
            # If image, check for content-length > 4K
            size = url.clength
            return (size>self.size_threshold)
```

The function simply tells the crawler to alway save non-Image URLs, by
returning True. For image URLs, it checks for size and returns True
only if the size is greater than the required threshold size, else False.

The main object here of interest is the **_event_** object. This object contains
all the state the programmer needs to write the custom behavior. The _event_
object is of type **_Event_**, a class defined in the module _harvestman.lib.event_.

The _Event_ class is defined as follows.
```
class Event(object):
    """ Event class for HarvestMan """

    def __init__(self):
        self.name = ''
        self.config = objects.config
        self.url = None
        self.document = None
```

The attributes of the class are namely, _name_, _config_, _url_ and _document_. Of these the attributes of primary interest to the developer are _url_ and _document_.

### The _url_ attribute ###
The _url_ attribute contains the current URL object which is being processed. The URL object is of type _HarvestManUrl_ (in module _harvestman.lib.urlparser_). It keeps
all the state of the current URL under processing.

### The _document_ attribute ###
The _document_ attribute holds information on the current web-page being crawled.
The _document_ object is of type _HarvestManDocument_ (module _harvestman.lib.document_). This object holds information on the URL as a document, i.e its content, etag, last modified time etc. The document object is useful for URLs which represent web-pages or documents such as PDF etc.

### The _config_ attribute ###
This attribute binds to the global configuration object. Instead of having to call _objects.config_ everytime, you can get global configuration in the event handler by accessing the _event.config_ attribute.

### The _name_ attribute ###
This will contain the name of the event. For example in the above code, this would be _save\_url\_data_.

### How to use attributes of _event_ object ###
For most events, the _url_ attribute it present and is required to do any meaningful processing. The _document_ attribute is present only for the events which are dealing with a web-page with parseable content. For some events which are related to program
stages (such as start/end of a project), both these attributes wont be present, i.e they will be _None_.

### Additional arguments ###
Additional arguments could be passed to the event handler by specific events. Positional arguments will appear as the _`*args`_ and keyword arguments as the _`**kwargs`_ variables respectively. For example the _before\_tag\_parse_ event passes in the current HTML tag and its attributes using positional arguments.



## Table of Events ##
The following table lists the main events raised by HarvestMan and the attributes that are filled in for each event, additional arguments, points in program flow when the events are raised, module which raises the event etc.

| **Event** | **Raised when** | **Attributes** | **Positional Arguments** | **Module** | **Comments** |
|:----------|:----------------|:---------------|:-------------------------|:-----------|:-------------|
| before\_start\_project | Before starting a project | _url_ | None | _harvestman.apps.spider_ | _url_ is the starting URL |
| post\_start\_project | After starting a project | _url_ | None | _harvestman.apps.spider_  | _url_ is the starting URL |
| before\_finish\_project | Before finishing a project | _url_ | None| _harvestman.apps.spider_ | _url_ is the starting URL |
| after\_finish\_project | After finishing a project | _url_ | None |_harvestman.apps.spider_ | _url_ is the starting URL |
| before\_crawl\_url | Before a URL is crawled | _url_, _document_ | None | _harvestman.lib.crawler_ | _crawled_ here means the function _crawl\_url_ |
| post\_crawl\_url | After a URL is crawled | _url_, _document_ | None | _harvestman.lib.crawler_ | _crawled_ here means the function _crawl\_url_ |
| before\_download\_url | Before a URL is downloaded | _url_ | None | _harvestman.lib.crawler_ |  |
| before\_parse\_url | Before a URL is parsed | _url_,_document_ | None | _harvestman.lib.crawler_ | This always comes after _before\_download\_url_ hook |
| post\_parse\_url | After a URL is parsed | _url_,_document_ | _links_ | _harvestman.lib.crawler_ | _links_ stand for the child links of this URL |
| before\_url\_connect | Before connection for a URL is done | _url_ | _last\_modified_, _etag_ | _harvestman.lib.connector_ | last\_modified, etag args are valid (not None) only if there is cache for the URL |
| post\_url\_connect | After connection for a URL is done | _url_ | None | _harvestman.lib.connector_ |  |
| save\_url\_data | Before saving data for a URL to disk | _url_ | _data_ | _harvestman.lib.connector_ | _data_ is the content of the URL |
| post\_crawl\_complete | After the crawl is completed | None | None | _harvestman.lib.datamgr_ |  |
| before\_tag\_parse | Before an HTML tag is parsed | _url_ | _tag_,_attrs_ | _harvestman.lib.pageparser_ | _tag_ is the tag name and _attrs_ the attributes dictionary |
| before\_tag\_data | Before CDATA of an HTML tag is parsed | _url_ | _tag_, _cdata_ | _harvestman.lib.pageparser_ | _tag_ is the tag name and _cdata_ is its CDATA |
| include\_this\_url | Before a URL is checked for rules | _url_ | None | _harvestman.lib.rules_ | This comes before a URL is crawled |

## Programming using Events ##
The key towards programming with events is that, the programmer can control the program flow by binding to any _before_ event and returning True or False depending upon his logic.

All events which are raised **before** a certain action is performed, checks for the return value of the event processing. **_If the return value is False, the rest of the processing in the function which raised the event is NOT done_**. **_If the return value is True, the function continues processing as if nothing happened_**.

This can be exploited to write custom crawlers that perform specific actions. For example in the sample code illustrated previously, we return _True_ if the URL is not an image and _False_ if the URL is an image, but below the given size. This way we modify the functionality of the function which raised the event, thereby causing the program to not save image URLs below a certain size.

_Post_ events (events raised after an action, check table) are also useful, but since their return values are not checked in code, they are much less useful in controlling program flow when compared to _pre_ events.

_NOTE_: In the table, any event for which _Raised when_ says _before_ is a pre-event. Any event for which it says _post_ or _after_ is a post-event.

## More Reading ##
For more information, check out sample custom crawler applications in the folder [\_harvestman/apps/samples\_](http://code.google.com/p/harvestman-crawler/source/browse/#svn/trunk/HarvestMan-lite/harvestman/apps/samples) in the code-base. Also read the HOWTO at [\_doc/events.HOWTO\_](http://code.google.com/p/harvestman-crawler/source/browse/trunk/HarvestMan-lite/doc/events.HOWTO).

## Caveat ##
In the earlier released versions, the _register_ method is not present. Instead the method name is _bind\_event_, with the same arguments. Also in released versions, positional arguments are not supported and additional arguments are always passed in as keyword arguments. This document is conformant to the most recent release (HarvestMan 2.0.5 beta) and the current trunk-code under HarvestMan-lite branch.


