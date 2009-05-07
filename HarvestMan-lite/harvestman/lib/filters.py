# -- coding: utf-8
"""
filters.py - Module which holds class definitions for
classes which define filters for filtering out URLs
and web pages based on regualr expression and other kinds
of filters.

 Author: Anand B Pillai <abpillai at gmail dot com>

 Modification History
 --------------------

 Jul 23 2008 Anand   Creation
 Nov 17 2008 Anand   Completed URL filters class implementation
                     and integrated with HarvestMan.
 Jan 13 2009 Anand   Added text filter class. Modified
                     junk filter class to follow the filter
                     class interface.
 
  Copyright (C) 2003-2008 Anand B Pillai.
                                
"""
import re
from harvestman.lib.common.common import *

class HarvestManBaseFilter(object):
    """ Base class for all HarvestMan filter classes """

    def __init__(self):
        self.context = None
        
    def filter(self, url):
        raise NotImplementedError

    def make_regex(self, pattern, casing, flags):

        flag = 0
        if not casing:
            flag |= re.IGNORECASE
        if flags:
            flag |= eval(flags)

        return re.compile(pattern, flag)
        
class HarvestManUrlFilter(HarvestManBaseFilter):
    """ Filter class for filtering out web pages based on the URL path string """

    def __init__(self, pathfilters=[], extnfilters=[], regexfilters=[]):
        # Filter pattern strings
        self.regexfilterpatterns = regexfilters
        self.pathfilterpatterns = pathfilters
        self.extnfilterpatterns = extnfilters
        # Intermediate patterns, dictionaries
        # with keys 'include' and 'exclude'
        self.regexpatterns = []
        self.pathpatterns = { 'include': [], 'exclude': [] }
        self.extnpatterns = { 'include': [], 'exclude': [] }
        # Actual filters
        self.inclfilters = []
        self.exclfilters = []
        self.compile_filters()

    def parse_filter(self, filterstring):
        """ Parse a filter pattern string and return a two
        tuple of (<inclusion>, <exclusion>) pattern string
        lists """

        fstr = filterstring
        # First replace any ''' with ''
        fstr=fstr.replace("'",'')            
        # regular expressions to include
        include=[]
        # regular expressions to exclude        
        exclude=[]

        index=0
        previndex=-1
        fstr += '+'
        for c in fstr:
            if c in ('+','-'):
                previndex=index
            index+=1

        l=fstr.split('+')

        for s in l:
            l2=s.split('-')
            for x in xrange(len(l2)):
                s=l2[x]
                if s=='': continue
                if x==0:
                    include.append(s)
                else:
                    exclude.append(s)

        return (include, exclude)

    def create_filter(self, plainstr, extn=False):
        """ Create a python regular expression based on
        the list of filter strings provided as input """

        # Final filter string
        fstr = ''
        s = plainstr
        
        # First replace any ''' with ''
        s=s.replace("'",'')            
        # Then we remove the asteriks
        s=s.replace('*','.*')
        fstr = s

        if extn:
            fstr = '\.' + fstr + '$'

        return fstr
        
    def make_path_filter(self, filterstring, casing=0, flags=''):
        """ Creates a URL path filter. A URL path is specified
        as an include/exclude filter. Wildcards are specified by
        using asteriks """
        
        include, exclude = self.parse_filter(filterstring)
        
        for pattern in include:
            self.pathpatterns['include'].append((self.create_filter(pattern), casing, flags))
        for pattern in exclude:
            self.pathpatterns['exclude'].append((self.create_filter(pattern), casing, flags))

    def make_extn_filter(self, filterstring, casing=0, flags=''):
        """ Creates a file extension filter. A file extension filter
        is specified by concatenating file extensions with a + or - in
        front of them to specify include/exclude respectively """
        
        include, exclude = self.parse_filter(filterstring)
        
        for pattern in include:
            self.extnpatterns['include'].append((self.create_filter(pattern, True), casing, flags))
        for pattern in exclude:
            self.extnpatterns['exclude'].append((self.create_filter(pattern, True), casing, flags))

    def make_regex_filter(self, filterstring, casing=0, flags=''):
        """ Creates a regular expression filter. This is nothing but a Python
        regular expression string which is compiled directly into a regex """
        
        # Direct use - no processing required
        self.regexpatterns.append((filterstring, casing, flags))
        
    def compile_filters(self):
        """ Compile all filter strings and create regular
        expression objects """
        
        for pattern, casing, flags in self.pathfilterpatterns:
            self.make_path_filter(pattern, casing, flags)

        for pattern, casing, flags in self.extnfilterpatterns:
            self.make_extn_filter(pattern, casing, flags)            
            
        for pattern, casing, flags in self.regexfilterpatterns:
            self.make_regex_filter(pattern, casing, flags)

        # Now, compile each to regular expressions and
        # append to include & exclude regex filter list
        for urlfilter in self.pathpatterns['include'] + self.extnpatterns['include']:
            regexp = self.make_regex(urlfilter[0], urlfilter[1], urlfilter[2])
            self.inclfilters.append(regexp)
            
        for urlfilter in self.pathpatterns['exclude'] + self.extnpatterns['exclude']:
            regexp = self.make_regex(urlfilter[0], urlfilter[1], urlfilter[2])
            self.exclfilters.append(regexp)

        for urlfilter in self.regexpatterns:
            regexp = self.make_regex(urlfilter[0], urlfilter[1], urlfilter[2])
            self.exclfilters.append(regexp)            

    def filter(self, urlobj):
        """ Apply all URL filters on the passed URL object 'urlobj'.
        Return True if filtered and False if not filtered """

        # The logic of this is simple - The URL is checked
        # against all inclusion filters first, if any. If
        # anything matches, then we don't do exclusion filter
        # check since inclusion (+) has preference over exclusion (-)
        # In that case, False is returned.
        
        # Otherwise, the URL is checked against all exclusion
        # filters and if any match, True is returned.

        # Finally, if none match, False is returned.

        url = urlobj.get_full_url()
        matchincl, matchexcl = False, False

        for urlfilter in self.inclfilters:
            m = urlfilter.search(url)
            if m:
                debug("Inclusion filter for URL %s found", url)
                matchincl = True
                break

        if matchincl:
            return False

        for urlfilter in self.exclfilters:
            m = urlfilter.search(url)
            if m:
                debug("Exclusion filter for URL %s found", url)
                matchexcl = True
                break

        if matchexcl:
            return True

        return False

class HarvestManTextFilter(HarvestManBaseFilter):
    """ Filter class for filtering out web pages based on the URL path string """

    def __init__(self, contentfilters=[], metafilters=[]):
        # Filter pattern strings
        self.contentpatterns = contentfilters
        self.metapatterns = metafilters
        # print 'Content=>',self.contentpatterns
        # print 'Meta=>',self.metapatterns
        # Actual filters
        # Text filters are always exclude filters, so
        # no need of separate include & exclude keys
        self.contentfilter = []
        # Meta filters
        self.keywordfilter = []
        self.titlefilter = []
        self.descfilter = []
        # Parse and compile the filters
        self.compile_filters()

    def compile_filters(self):

        # Content filter is straight forward
        for pattern, casing, flags in self.contentpatterns:
            self.contentfilter.append(self.make_regex(pattern, casing, flags))

        # Some pre-processing is involved in meta-filters
        for pattern,casing,flags,tags in self.metapatterns:
            regex = self.make_regex(pattern, casing, flags)
            if tags=='all':
                # Append to all filters
                self.keywordfilter.append(regex)
                self.titlefilter.append(regex)
                self.descfilter.append(regex)
            else:
                # Split and see which all tags are specified
                tagslist = tags.split(',')
                if 'title' in tagslist:
                    self.titlefilter.append(regex)
                if 'keywords' in tagslist:
                    self.keywordfilter.append(regex)
                if 'description' in tagslist:
                    self.descfilter.append(regex)                    


    def filter(self, urldoc, urlobj):
        """ Apply all URL filters on the passed URL document object
        Return True if filtered and False if not filtered """

        filterurl = False
        
        # Apply content filter
        for cfilter in self.contentfilter:
            m = cfilter.search(urldoc.content)
            if m:
                debug("Content filter for URL %s found" % urlobj)
                self.context='Content'
                return True

        # Apply meta filters
        for tfilter in self.titlefilter:
            m = tfilter.search(urldoc.title)
            if m:
                debug("Title filter for URL %s found" % urlobj)
                self.context='Title'                
                return True

        for dfilter in self.descfilter:
            m = dfilter.search(urldoc.description)
            if m:
                debug("Description filter for URL %s found" % urlobj)
                self.context='Description'                
                return True            
            
        for kfilter in self.keywordfilter:
            matches = [kfilter.search(keyword) for keyword in urldoc.keywords]
            if len(matches):
                debug("Keyword filter for URL %s found" % urlobj)
                self.context='Keyword'                
                return True

        return False
                   
class HarvestManJunkFilter(HarvestManBaseFilter):
    """ Junk filter class. Filter out junk urls such
    as ads, banners, flash files etc """

    # Domain specific blocking - List courtesy
    # junkbuster proxy.
    block_domains =[ '1ad.prolinks.de',
                     '1st-fuss.com',
                     '247media.com',
                     'admaximize.com',
                     'adbureau.net',
                     'adsolution.de',
                     'adwisdom.com',
                     'advertising.com',
                     'atwola.com',
                     'aladin.de',
                     'annonce.insite.dk',
                     'a.tribalfusion.com',                           
                     'avenuea.com',
                     'bannercommunity.de',
                     'banerswap.com',
                     'bizad.nikkeibp.co.jp',
                     'bluestreak.com',
                     'bs.gsanet.com',
                     'cash-for-clicks.de',
                     'cashformel.com',                           
                     'cash4banner.de',
                     'cgi.tietovalta.fi',
                     'cgicounter.puretec.de',
                     'click-fr.com',
                     'click.egroups.com',
                     'commonwealth.riddler.com',
                     'comtrack.comclick.com',
                     'customad.cnn.com',
                     'cybereps.com:8000',
                     'cyberclick.net',
                     'dino.mainz.ibm.de',
                     'dinoadserver1.roka.net',
                     'disneystoreaffiliates.com',
                     'dn.adzerver.com',
                     'doubleclick.net',
                     'ds.austriaonline.at',
                     'einets.com',
                     'emap.admedia.net',
                     'eu-adcenter.net',
                     'eurosponser.de',
                     'fastcounter.linkexchange.com',
                     'findcommerce.com',
                     'flycast.com',
                     'focalink.com',
                     'fp.buy.com',
                     'globaltrack.com',
                     'globaltrak.net',
                     'gsanet.com',                           
                     'hitbox.com',
                     'hurra.de',
                     'hyperbanner.net',
                     'iadnet.com',
                     'image.click2net.com',
                     'image.linkexchange.com',
                     'imageserv.adtech.de',
                     'imagine-inc.com',
                     'img.getstats.com',
                     'img.web.de',
                     'imgis.com',
                     'james.adbutler.de',
                     'jmcms.cydoor.com',
                     'leader.linkexchange.com',
                     'linkexchange.com',
                     'link4ads.com',
                     'link4link.com',
                     'linktrader.com',
                     'media.fastclick.net',
                     'media.interadnet.com',
                     'media.priceline.com',
                     'mediaplex.com',
                     'members.sexroulette.com',
                     'newsads.cmpnet.com',
                     'ngadcenter.net',
                     'nol.at:81',
                     'nrsite.com',
                     'offers.egroups.com',
                     'omdispatch.co.uk',
                     'orientserve.com',
                     'pagecount.com',
                     'preferences.com',
                     'promotions.yahoo.com',
                     'pub.chez.com',
                     'pub.nomade.fr',
                     'qa.ecoupons.com',
                     'qkimg.net',
                     'resource-marketing.com',
                     'revenue.infi.net',
                     'sam.songline.com',
                     'sally.songline.com',
                     'sextracker.com',
                     'smartage.com',
                     'smartclicks.com',
                     'spinbox1.filez.com',
                     'spinbox.versiontracker.com',
                     'stat.onestat.com',
                     'stats.surfaid.ihost.com',
                     'stats.webtrendslive.com',
                     'swiftad.com',
                     'tm.intervu.net',
                     'tracker.tradedoubler.com',
                     'ultra.multimania.com',
                     'ultra1.socomm.net',
                     'uproar.com',
                     'usads.imdb.com',
                     'valueclick.com',
                     'valueclick.net',
                     'victory.cnn.com',
                     'videoserver.kpix.com',
                     'view.atdmt.com',
                     'webcounter.goweb.de',
                     'websitesponser.de',
                     'werbung.guj.de',
                     'wvolante.com',
                     'www.ad-up.com',
                     'www.adclub.net',
                     'www.americanpassage.com',
                     'www.bannerland.de',
                     'www.bannermania.nom.pl',
                     'www.bizlink.ru',
                     'www.cash4banner.com',                           
                     'www.clickagents.com',
                     'www.clickthrough.ca',
                     'www.commision-junction.com',
                     'www.eads.com',
                     'www.flashbanner.no',                           
                     'www.mediashower.com',
                     'www.popupad.net',                           
                     'www.smartadserver.com',                           
                     'www.smartclicks.com:81',
                     'www.spinbox.com',
                     'www.sponsorpool.net',
                     'www.ugo.net',
                     'www.valueclick.com',
                     'www.virtual-hideout.net',
                     'www.web-stat.com',
                     'www.webpeep.com',
                     'www.zserver.com',
                     'www3.exn.net:80',
                     'xb.xoom.com',
                     'yimg.com' ]

    # Common block patterns. These are created
    # in the Python regular expression syntax.
    # Original list courtesy junkbuster proxy.
    block_patterns = [ r'/*.*/(.*[-_.])?ads?[0-9]?(/|[-_.].*|\.(gif|jpe?g))',
                       r'/*.*/(.*[-_.])?count(er)?(\.cgi|\.dll|\.exe|[?/])',
                       r'/*.*/(.*[-_.].*)?maino(kset|nta|s).*(/|\.(gif|html?|jpe?g|png))',
                       r'/*.*/(ilm(oitus)?|kampanja)(hallinta|kuvat?)(/|\.(gif|html?|jpe?g|png))',
                       r'/*.*/(ng)?adclient\.cgi',
                       r'/*.*/(plain|live|rotate)[-_.]?ads?/',
                       r'/*.*/(sponsor|banner)s?[0-9]?/',
                       r'/*.*/*preferences.com*',
                       r'/*.*/.*banner([-_]?[a-z0-9]+)?\.(gif|jpg)',
                       r'/*.*/.*bannr\.gif',
                       r'/*.*/.*counter\.pl',
                       r'/*.*/.*pb_ihtml\.gif',
                       r'/*.*/Advertenties/',
                       r'/*.*/Image/BannerAdvertising/',
                       r'/*.*/[?]adserv',
                       r'/*.*/_?(plain|live)?ads?(-banners)?/',
                       r'/*.*/abanners/',
                       r'/*.*/ad(sdna_image|gifs?)/',
                       r'/*.*/ad(server|stream|juggler)\.(cgi|pl|dll|exe)',
                       r'/*.*/adbanner*',
                       r'/*.*/adfinity',
                       r'/*.*/adgraphic*',
                       r'/*.*/adimg/',
                       r'/*.*/adjuggler',
                       r'/*.*/adlib/server\.cgi',
                       r'/*.*/ads\\',
                       r'/*.*/adserver',
                       r'/*.*/adstream\.cgi',
                       r'/*.*/adv((er)?ts?|ertis(ing|ements?))?/',
                       r'/*.*/advanbar\.(gif|jpg)',
                       r'/*.*/advanbtn\.(gif|jpg)',
                       r'/*.*/advantage\.(gif|jpg)',
                       r'/*.*/amazon([a-zA-Z0-9]+)\.(gif|jpg)',
                       r'/*.*/ana2ad\.gif',
                       r'/*.*/anzei(gen)?/?',
                       r'/*.*/ban[-_]cgi/',
                       r'/*.*/banner_?ads/',
                       r'/*.*/banner_?anzeigen',
                       r'/*.*/bannerimage/',
                       r'/*.*/banners?/',
                       r'/*.*/banners?\.cgi/',
                       r'/*.*/bizgrphx/',
                       r'/*.*/biznetsmall\.(gif|jpg)',
                       r'/*.*/bnlogo.(gif|jpg)',
                       r'/*.*/buynow([a-zA-Z0-9]+)\.(gif|jpg)',
                       r'/*.*/cgi-bin/centralad/getimage',
                       r'/*.*/drwebster.gif',
                       r'/*.*/epipo\.(gif|jpg)',
                       r'/*.*/gsa_bs/gsa_bs.cmdl',
                       r'/*.*/images/addver\.gif',
                       r'/*.*/images/advert\.gif',
                       r'/*.*/images/marketing/.*\.(gif|jpe?g)',
                       r'/*.*/images/na/us/brand/',
                       r'/*.*/images/topics/topicgimp\.gif',
                       r'/*.*/phpAds/phpads.php',
                       r'/*.*/phpAds/viewbanner.php',
                       r'/*.*/place-ads',
                       r'/*.*/popupads/',
                       r'/*.*/promobar.*',
                       r'/*.*/publicite/',
                       r'/*.*/randomads/.*\.(gif|jpe?g)',
                       r'/*.*/reklaam/.*\.(gif|jpe?g)',
                       r'/*.*/reklama/.*\.(gif|jpe?g)',
                       r'/*.*/reklame/.*\.(gif|jpe?g)',
                       r'/*.*/servfu.pl',
                       r'/*.*/siteads/',
                       r'/*.*/smallad2\.gif',
                       r'/*.*/spin_html/',
                       r'/*.*/sponsor.*\.gif',
                       r'/*.*/sponsors?[0-9]?/',
                       r'/*.*/ucbandeimg/',
                       r'/*.*/utopiad\.(gif|jpg)',
                       r'/*.*/werb\..*',
                       r'/*.*/werbebanner/',
                       r'/*.*/werbung/.*\.(gif|jpe?g)',
                       r'/*ad.*.doubleclick.net',
                       r'/.*(ms)?backoff(ice)?.*\.(gif|jpe?g)',
                       r'/.*./Adverteerders/',
                       r'/.*/?FPCreated\.gif',
                       r'/.*/?va_banner.html',
                       r'/.*/adv\.',
                       r'/.*/advert[0-9]+\.jpg',
                       r'/.*/favicon\.ico',
                       r'/.*/ie_?(buttonlogo|static?|anim.*)?\.(gif|jpe?g)',
                       r'/.*/ie_horiz\.gif',
                       r'/.*/ie_logo\.gif',
                       r'/.*/ns4\.gif',
                       r'/.*/opera13\.gif',
                       r'/.*/opera35\.gif',
                       r'/.*/opera_b\.gif',
                       r'/.*/v3sban\.gif',
                       r'/.*Ad00\.gif',
                       r'/.*activex.*(gif|jpe?g)',
                       r'/.*add_active\.gif',
                       r'/.*addchannel\.gif',
                       r'/.*adddesktop\.gif',
                       r'/.*bann\.gif',
                       r'/.*barnes_logo\.gif',
                       r'/.*book.search\.gif',
                       r'/.*by/main\.gif',
                       r'/.*cnnpostopinionhome.\.gif',
                       r'/.*cnnstore\.gif',
                       r'/.*custom_feature\.gif',
                       r'/.*exc_ms\.gif',
                       r'/.*explore.anim.*gif',
                       r'/.*explorer?.(gif|jpe?g)',
                       r'/.*freeie\.(gif|jpe?g)',
                       r'/.*gutter117\.gif',
                       r'/.*ie4_animated\.gif',
                       r'/.*ie4get_animated\.gif',
                       r'/.*ie_sm\.(gif|jpe?g)',
                       r'/.*ieget\.gif',
                       r'/.*images/cnnfn_infoseek\.gif',
                       r'/.*images/pathfinder_btn2\.gif',
                       r'/.*img/gen/fosz_front_em_abc\.gif',
                       r'/.*img/promos/bnsearch\.gif',
                       r'/.*infoseek\.gif',
                       r'/.*logo_msnhm_*',
                       r'/.*mcsp2\.gif',
                       r'/.*microdell\.gif',
                       r'/.*msie(30)?\.(gif|jpe?g)',
                       r'/.*msn2\.gif',
                       r'/.*msnlogo\.(gif|jpe?g)',
                       r'/.*n_iemap\.gif',
                       r'/.*n_msnmap\.gif',
                       r'/.*navbars/nav_partner_logos\.gif',
                       r'/.*nbclogo\.gif',
                       r'/.*office97_ad1\.(gif|jpe?g)',
                       r'/.*pathnet.warner\.gif',
                       r'/.*pbbobansm\.(gif|jpe?g)',
                       r'/.*powrbybo\.(gif|jpe?g)',
                       r'/.*s_msn\.gif',
                       r'/.*secureit\.gif',
                       r'/.*sqlbans\.(gif|jpe?g)',
                       r'/BannerImages/'
                       r'/BarnesandNoble/images/bn.recommend.box.*',
                       r'/Media/Images/Adds/',
                       r'/SmartBanner/',
                       r'/US/AD/',
                       r'/_banner/',
                       r'/ad[-_]container/',
                       r'/adcycle.cgi',
                       r'/adcycle/',
                       r'/adgenius/',
                       r'/adimages/',
                       r'/adproof/',
                       r'/adserve/',
                       r'/affiliate_banners/',
                       r'/annonser?/',
                       r'/anz/pics/',
                       r'/autoads/',
                       r'/av/gifs/av_logo\.gif',
                       r'/av/gifs/av_map\.gif',
                       r'/av/gifs/new/ns\.gif',
                       r'/bando/',
                       r'/bannerad/',
                       r'/bannerfarm/',
                       r'/bin/getimage.cgi/...\?AD',
                       r'/cgi-bin/centralad/',
                       r'/cgi-bin/getimage.cgi/....\?GROUP=',
                       r'/cgi-bin/nph-adclick.exe/',
                       r'/cgi-bin/nph-load',
                       r'/cgi-bin/webad.dll/ad',
                       r'/cgi/banners.cgi',
                       r'/cwmail/acc\.gif',
                       r'/cwmail/amzn-bm1\.gif',
                       r'/db_area/banrgifs/',
                       r'/digitaljam/images/digital_ban\.gif',
                       r'/free2try/',
                       r'/gfx/bannerdir/',
                       r'/gif/buttons/banner_.*',
                       r'/gif/buttons/cd_shop_.*',
                       r'/gif/cd_shop/cd_shop_ani_.*',
                       r'/gif/teasere/',
                       r'/grafikk/annonse/',
                       r'/graphics/advert',
                       r'/graphics/defaultAd/',
                       r'/grf/annonif',
                       r'/hotstories/companies/images/companies_banner\.gif',
                       r'/htmlad/',
                       r'/image\.ng/AdType',
                       r'/image\.ng/transactionID',
                       r'/images/.*/.*_anim\.gif',
                       r'/images/adds/',
                       r'/images/getareal2\.gif',
                       r'/images/locallogo.gif',
                       r'/img/special/chatpromo\.gif',
                       r'/include/watermark/v2/',
                       r'/ip_img/.*\.(gif|jpe?g)',
                       r'/ltbs/cgi-bin/click.cgi',
                       r'/marketpl*/',
                       r'/markets/images/markets_banner\.gif',
                       r'/minibanners/',
                       r'/ows-img/bnoble\.gif',
                       r'/ows-img/nb_Infoseek\.gif',
                       r'/p/d/publicid',
                       r'/pics/amzn-b5\.gif',
                       r'/pics/getareal1\.gif',
                       r'/pics/gotlx1\.gif',
                       r'/promotions/',
                       r'/rotads/',
                       r'/rotations/',
                       r'/torget/jobline/.*\.gif'
                       r'/viewad/'
                       r'/we_ba/',
                       r'/werbung/',
                       r'/world-banners/',
                       r'/worldnet/ad\.cgi',
                       r'/zhp/auktion/img/' ]
                            

    def __init__(self):
        self.msg = '<No Error>'
        self.match = ''
        # Compile pattern list for performance
        self.patterns = map(re.compile, self.block_patterns)
        # Create base domains list from domains list
        self.base_domains = map(self.base_domain, self.block_domains)

    def reset_msg(self):
        self.msg = '<No Error>'

    def reset_match(self):
        self.msg = ''        
        
    def filter(self, urlobj):
        """ Apply Junk filter on the passed URL object. Return True
        if filtered and False if not filtered """

        self.reset_msg()
        self.reset_match()
        
        # Check domain first
        ret = self._check_domain(urlobj)
        if ret:
            return ret

        # Check pattern next
        return self._check_pattern(urlobj)

    def base_domain(self, domain):

        if domain.count(".") > 1:
            strings = domain.split(".")
            return "".join((strings[-2], strings[-1]))
        else:
            return domain
            
    def _check_domain(self, url_obj):
        """ Check whether the url belongs to a junk
        domain. Return true if url is O.K (NOT a junk
        domain) and False otherwise """

        # Get base server of the domain with port
        base_domain_port = url_obj.get_base_domain_with_port()
        # Get domain with port
        domain_port = url_obj.get_domain_with_port()

        # First check for domain
        if domain_port in self.block_domains:
            self.msg = '<Found domain match>'
            return True
        # Then check for base domain
        else:
            if base_domain_port in self.base_domains:
                self.msg = '<Found base-domain match>'                
                return True

        return False

    def _check_pattern(self, url_obj):
        """ Check whether the url matches a junk pattern.
        Return true if url is O.K (not a junk pattern) and
        false otherwise """

        url = url_obj.get_full_url()

        indx=0
        for p in self.patterns:
            # Do a search, not match
            if p.search(url):
                self.msg = '<Found pattern match>'
                self.match = self.block_patterns[indx]
                return True
            
            indx += 1
            
        return False
            
    def get_error_msg(self):
        return self.msg

    def get_match(self):
        return self.match
    
if __name__=="__main__":
    import urlparser
    
    # Test filter class
    filter = HarvestManJunkFilter()
    
    # Violates, should return False
    # The first two are direct domain matches, the
    # next two are base domain matches.
    u = urlparser.HarvestManUrl("http://a.tribalfusion.com/images/1.gif")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    u = urlparser.HarvestManUrl("http://stats.webtrendslive.com/cgi-bin/stats.pl")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    u = urlparser.HarvestManUrl("http://stats.cyberclick.net/cgi-bin/stats.pl")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()    
    u = urlparser.HarvestManUrl("http://m.doubleclick.net/images/anim.gif")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    
    # The next are pattern matches
    u = urlparser.HarvestManUrl("http://www.foo.com/popupads/ad.gif")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    print '\tMatch=>',filter.get_match()
    u = urlparser.HarvestManUrl("http://www.foo.com/htmlad/1.html")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    print '\tMatch=>',filter.get_match()    
    u = urlparser.HarvestManUrl("http://www.foo.com/logos/nbclogo.gif")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    print '\tMatch=>',filter.get_match()    
    u = urlparser.HarvestManUrl("http://www.foo.com/bar/siteads/1.ad")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    print '\tMatch=>',filter.get_match()    
    u = urlparser.HarvestManUrl("http://www.foo.com/banners/world-banners/banner.gif")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    print '\tMatch=>',filter.get_match()
    u = urlparser.HarvestManUrl("http://ads.foo.com/")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    print '\tMatch=>',filter.get_match()    
    
    
    # This one should not match
    u = urlparser.HarvestManUrl("http://www.foo.com/doc/logo.gif")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()
    # This also...
    u = urlparser.HarvestManUrl("http://www.foo.org/bar/vodka/pattern.html")
    print filter.filter(u),filter.get_error_msg(),'=>',u.get_full_url()    

