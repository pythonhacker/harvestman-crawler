# Harvestman config.xml #
## Configuration File Structure ##

The configuration file has different categories inside that split the configuration options into different sections. At present, the configuration file has the following namespaces:

  1. **project** - This section holds the options related to the current HarvestMan project
  1. **network** - This section holds the configuration options related to your network connection
  1. **download** - This section holds configuration option that affect your downloads in a generic way
  1. **control** - This section is similar to the above one, but holds options that affect your downloads in a much more specific way. This is a kind of 'tweak' section, that allows you to exert more fine-grained control over your projects.
  1. **system** - This section controls the threading options, regional (locale) options and any other options related to Python interpreter and your computer.
  1. **indexer** - This section holds variables related to how the files are processed after downloading. Right now it holds variables related to localizing links.
  1. **files** - This section holds variables that control the files created by HarvestMan namely error log, message log and an optional url log.
  1. **display** - This holds a single variable related to creating a browser page for all HarvestMan projects on your computer.

## Control Section ##
### fetchlevel ###

HarvestMan defines five fetchlevels with values ranging from 0 - 4 inclusive. These define the rules for the download of files in different servers other the server of the starting URL. In general **increasing a fetch level allows the program to crawl more files** on the Internet.

A fetchlevel of "0" provides the maximum constraint for the download. This limits the download of files to all paths in the starting server, only inside and below the directory of the starting URL.

For example, with a fetchlevel of zero, if you starting url is http://www.foo.com/bar/images/images.html, the program will download only those files inside the 

&lt;images&gt;

 sub-directory and directories below it, and no other file.

The next level, a fetch level of "1", again limits the download to the starting server (and sub-domains in it, if the sub-domain variable is not set), but does not allow it to crawl sites other than the starting server. In the above example, this will fetch all links in the server http://www.foo.com, encountered in the starting page.

A fetch level of "2" performs a fetching of all links in the starting server encountered in the starting URL, as well as any links in outside (external) servers linked directly from pages in the starting server. It does not allow the program to crawl pages linked further away, i.e the second-level links linked from the external servers.

A fetch level of "3", performs a similar operation with the main difference that it acts like a combination of fetchlevels "0" and "2" minus "1". That is, it gets all links under the directory of the starting URL and first level external links, but does not fetch links outside the directory of the starting URL.

A fetch level of "4" gives the user no control over the levels of fetching, and the program will crawl whichever link is available to it unless not limited by other download control options like depth control, domain filters ,url filters, file limits, maximum server limit etc.

Place the paramter in **control** element under **extent** section.
Here is a sample XML element including this new param.
```
 <control>
    ...
      <extent>
        <fetchlevel value="0"/>
        <depth value="10"/>
        <extdepth value="0"/>
        <subdomain value="0"/>
        <ignoretlds value="0"/>
      </extent>
    ...
 </control>
```


**The value can be 0,1,2,3,4**

See FAQ for more explanations.

### maxbandwidth ###
MaxBandwidth controls the speed of crawling. The throttling of bandwidth is used when we are downloading huge amount of data from a host. MaxBandwidh should prevent user from "Denial Of Service" that one could impose on the crawled server. By using this configuration variable you can limit your download speed to 5kb per second. With this speed the host should not have any problems serving your crawl and be able to proceed with its normal operations.

Place the paramter in **control** element under **limits** section.
Here is a sample XML element including this new param.
```
<control>
....
   <limits>
       <maxextservers value="0"/>
       <maxextdirs value="0"/>
       <maxfiles value="100"/>
       <maxfilesize value="5242880"/>
       <connections value="5"/>
       <maxbandwidth value="5.0" />
       <timelimit value="-1"/>
   </limits>
...
</control>
```

**The value needs to be specified in kb/sec , not in bytes/sec.**

### maxbytes ###
MaxBytes controls how many bytes your crawl will download. The max bytes is used when we are downloading huge amount of data from a host, and in conjunction with MaxBandwidh we want to limit how much data we download. By using this configuration variable with maxbandwidth you can set your crawl to download 10mb at 5kb/s. With this fine grained control of your download size and speed the host should not have any problems serving your crawl and be able to proceed with its normal operations.

Place the paramter in **control** element under **limits** section.
Here is a sample XML element including this new param.
```
<control>
....
   <limits>
       <maxextservers value="0"/>
       <maxextdirs value="0"/>
       <maxfiles value="100"/>
       <maxfilesize value="5242880"/>
       <connections value="5"/>
       <maxbandwidth value="5.0" />
       <maxbytes value="10mb"/>
       <timelimit value="-1"/>
   </limits>
...
</control>
```

**The value accepts plain numbers(assumes bytes), KB, MB and GB.**
```
<maxbytes value="5000" /> - End crawl at 5000 bytes
<maxbytes value="10kb" /> - End crawl at 10kb 
<maxbytes value="50MB" /> - End crawl at 50 MB.
<maxbytes value="1GB" /> - End crawl at 1 GB.
```