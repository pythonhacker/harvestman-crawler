# -- coding: utf-8
""" Unit test for urlparser module

Created: Anand B Pillai <abpillai@gmail.com> Apr 17 2007

Mod   Anand         Sep 29 08      Fix for issue #24.

Copyright (C) 2007, Anand B Pillai.
"""

import test_base
import unittest
import sys, os

test_base.setUp()

class TestHarvestManUrl(unittest.TestCase):
    """ Unit test class for HarvestManUrl class """

    from lib.urlparser import HarvestManUrl

    # Basic test set
    l = [ HarvestManUrl('http://www.yahoo.com/photos/my photo.gif'),
          HarvestManUrl('http://www.rediff.com:80/r/r/tn2/2003/jun/25usfed.htm'),
          HarvestManUrl('http://cwc2003.rediffblogs.com'),
          HarvestManUrl('/sports/2003/jun/25beck1.htm',
                              'generic', 0, 'http://www.rediff.com', ''),
          HarvestManUrl('http://ftp.gnu.org/pub/lpf.README'),
          HarvestManUrl('http://www.python.org/doc/2.3b2'),
          HarvestManUrl('//images.sourceforge.net/div.png',
                              'image', 0, 'http://sourceforge.net', ''),
          HarvestManUrl('http://pyro.sourceforge.net/manual/LICENSE'),
          HarvestManUrl('python/test.htm', 'generic', 0,
                              'http://www.foo.com/bar/index.html', ''),
          HarvestManUrl('/python/test.css', 'generic',
                              0, 'http://www.foo.com/bar/vodka/test.htm', ''),
          HarvestManUrl('/visuals/standard.css', 'generic', 0,
                              'http://www.garshol.priv.no/download/text/perl.html'),
          HarvestManUrl('www.fnorb.org/index.html', 'generic',
                              0, 'http://pyro.sourceforge.net'),
          HarvestManUrl('http://profigure.sourceforge.net/index.html',
                              'generic', 0, 'http://pyro.sourceforge.net'),
          HarvestManUrl('#anchor', 'anchor', 0, 
                              'http://www.foo.com/bar/index.html'),
          HarvestManUrl('nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html#__init__#index-after', 'anchor', 0, 'http://nltk.sourceforge.net/lite/doc/api/term-index.html'),              
          HarvestManUrl('../icons/up.png', 'image', 0,
                              'http://www.python.org/doc/current/tut/node2.html',
                              ''),
          HarvestManUrl('../eway/library/getmessage.asp?objectid=27015&moduleid=160',
                              'generic',0,'http://www.eidsvoll.kommune.no/eway/library/getmessage.asp?objectid=27015&moduleid=160'),
          HarvestManUrl('fileadmin/dz.gov.si/templates/../../../index.php',
                              'generic',0,'http://www.dz-rs.si'),
          HarvestManUrl('http://www.evvs.dk/index.php?cPath=26&osCsid=90207c4908a98db6503c0381b6b7aa70','form',True,'http://www.evvs.dk'),
          HarvestManUrl('http://arstechnica.com/reviews/os/macosx-10.4.ars'),
          HarvestManUrl('http://www.fylkesmannen.no/../fmt_hoved.asp',baseurl='http://www.fylkesmannen.no/osloogakershu'),
          HarvestManUrl('http://www.example.com/display%3c%5d%2f?weight=1.0&article=fred&lang=en&size=100&country=in&q=&id='),
          HarvestManUrl('file:extension.css'),
          HarvestManUrl('file://home/anand/style.css'),
          HarvestManUrl('file://style.css'),
          HarvestManUrl('file:/home/anand/style.css'),
          HarvestManUrl('file:/home/anand/'),
          HarvestManUrl('file://home/anand/'),
          HarvestManUrl('/bar/',baseurl='http://www.foo.com')]

    # Second test set - For base URL containing a '?' in path
    h = HarvestManUrl('http://razor.occams.info/code/repo/?/govtrack/sec/')
    h2 = HarvestManUrl('http://razor.occams.info/code/repo/?/govtrack/sec/?')
    
    l2 = [ HarvestManUrl('coderef.c', baseurl=h),
           HarvestManUrl('?/govtrack/sec/coderef2.c',baseurl=h),
           HarvestManUrl("?/sec/coderef3.c", baseurl=h),
           HarvestManUrl("?sec/coderef4.c", baseurl=h),
           HarvestManUrl("sec/coderef5.c", baseurl=h),
           HarvestManUrl("/sec/coderef6.c", baseurl=h),
           HarvestManUrl("govtrack/sec/coderef7.c", baseurl=h),
           HarvestManUrl("govtrack/?/sec/../coderef8.c", baseurl=h),
           HarvestManUrl("http://www.foo.com/govtrack/./sec/?/id/../coderef9.c"),
           HarvestManUrl("../repo2/govtrack/./sec/?/id/../coderef10.c", baseurl=h),
           HarvestManUrl('../coderef11.c', baseurl=h),
           HarvestManUrl('govtrack/?/sec/coderef12.c', baseurl=h),
           HarvestManUrl('../govtrack2/?/../sec/.././sec/coderef13.c', baseurl=h),
           HarvestManUrl('?/govtrack/?/sec/coderef14.c', baseurl=h2),
           HarvestManUrl('../gotrack2/../sec/?/../?/./sec/coderef15.c', baseurl=h2)
           ]

    def test_filename(self):
        d = os.path.abspath(os.curdir)
        
        assert(self.l[0].get_full_filename()==os.path.join(d, 'www.yahoo.com/photos/my photo.gif'))
        assert(self.l[1].get_full_filename()==os.path.join(d, 'www.rediff.com/r/r/tn2/2003/jun/25usfed.htm'))
        assert(self.l[2].get_full_filename()==os.path.join(d, 'cwc2003.rediffblogs.com/index.html'))
        assert(self.l[3].get_full_filename()==os.path.join(d, 'www.rediff.com/sports/2003/jun/25beck1.htm'))
        assert(self.l[4].get_full_filename()==os.path.join(d, 'ftp.gnu.org/pub/lpf.README'))
        assert(self.l[5].get_full_filename()==os.path.join(d, 'www.python.org/doc/2.3b2'))
        assert(self.l[6].get_full_filename()==os.path.join(d, 'images.sourceforge.net/div.png'))
        assert(self.l[7].get_full_filename()==os.path.join(d, 'pyro.sourceforge.net/manual/LICENSE'))
        assert(self.l[8].get_full_filename()==os.path.join(d, 'www.foo.com/bar/python/test.htm'))
        assert(self.l[9].get_full_filename()==os.path.join(d, 'www.foo.com/python/test.css'))
        assert(self.l[10].get_full_filename()==os.path.join(d, 'www.garshol.priv.no/visuals/standard.css'))
        assert(self.l[11].get_full_filename()==os.path.join(d, 'www.fnorb.org/index.html'))
        assert(self.l[12].get_full_filename()==os.path.join(d, 'profigure.sourceforge.net/index.html'))
        assert(self.l[13].get_full_filename()==os.path.join(d, 'www.foo.com/bar/index.html'))
        assert(self.l[14].get_full_filename()==os.path.join(d, 'nltk.sourceforge.net/lite/doc/api/nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html'))
        assert(self.l[15].get_full_filename()==os.path.join(d, 'www.python.org/doc/current/icons/up.png'))
        assert(self.l[16].get_full_filename()==os.path.join(d, 'www.eidsvoll.kommune.no/eway/eway/library/getmessage.aspobjectid=27015&moduleid=160'))
        assert(self.l[17].get_full_filename()==os.path.join(d, 'www.dz-rs.si/index.php'))
        assert(self.l[18].get_full_filename()==os.path.join(d, 'www.evvs.dk/index.phpcPath=26&osCsid=90207c4908a98db6503c0381b6b7aa70'))
        assert(self.l[19].get_full_filename()==os.path.join(d, 'arstechnica.com/reviews/os/macosx-10.4.ars/index.html'))
        assert(self.l[20].get_full_filename()==os.path.join(d, 'www.fylkesmannen.no/fmt_hoved.asp'))
        assert(self.l[21].get_full_filename()==os.path.join(d, 'www.example.com/display]weight=1.0&article=fred&lang=en&size=100&country=in&q=&id='))
        
    def test_valid_filename(self):

        assert(self.l[0].validfilename=='my photo.gif')
        assert(self.l[1].validfilename=='25usfed.htm')
        assert(self.l[2].validfilename=='index.html')
        assert(self.l[3].validfilename=='25beck1.htm')
        assert(self.l[4].validfilename=='lpf.README')
        assert(self.l[5].validfilename=='2.3b2')
        assert(self.l[6].validfilename=='div.png')
        assert(self.l[7].validfilename=='LICENSE')
        assert(self.l[8].validfilename=='test.htm')
        assert(self.l[9].validfilename=='test.css')
        assert(self.l[10].validfilename=='standard.css')
        assert(self.l[11].validfilename=='index.html')
        assert(self.l[12].validfilename=='index.html')
        assert(self.l[13].validfilename=='index.html')
        assert(self.l[14].validfilename=='nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html')
        assert(self.l[15].validfilename=='up.png')
        assert(self.l[16].validfilename=='getmessage.aspobjectid=27015&moduleid=160')
        assert(self.l[17].validfilename=='index.php')
        assert(self.l[18].validfilename=='index.phpcPath=26&osCsid=90207c4908a98db6503c0381b6b7aa70')
        assert(self.l[19].validfilename=='index.html')
        assert(self.l[20].validfilename=='fmt_hoved.asp')
        assert(self.l[21].validfilename=='display]weight=1.0&article=fred&lang=en&size=100&country=in&q=&id=')
        

    def test_is_relative_path(self):

        assert(self.l[0].is_relative_path()==False)
        assert(self.l[1].is_relative_path()==False)
        assert(self.l[2].is_relative_path()==False)
        assert(self.l[3].is_relative_path()==True)
        assert(self.l[4].is_relative_path()==False)
        assert(self.l[5].is_relative_path()==False)
        assert(self.l[6].is_relative_path()==False)
        assert(self.l[7].is_relative_path()==False)
        assert(self.l[8].is_relative_path()==True)
        assert(self.l[9].is_relative_path()==True)
        assert(self.l[10].is_relative_path()==True)
        assert(self.l[11].is_relative_path()==False)
        assert(self.l[12].is_relative_path()==False)
        assert(self.l[13].is_relative_path()==False)
        assert(self.l[14].is_relative_path()==True)
        assert(self.l[15].is_relative_path()==True)
        assert(self.l[16].is_relative_path()==True)
        assert(self.l[17].is_relative_path()==True)
        assert(self.l[18].is_relative_path()==False)
        assert(self.l[19].is_relative_path()==False)
        assert(self.l[20].is_relative_path()==False)
        assert(self.l[21].is_relative_path()==False)        
        
    def test_absolute_url(self):

        assert(self.l[0].get_full_url()=='http://www.yahoo.com/photos/my%20photo.gif')
        assert(self.l[1].get_full_url()=='http://www.rediff.com/r/r/tn2/2003/jun/25usfed.htm')
        assert(self.l[2].get_full_url()=='http://cwc2003.rediffblogs.com/')
        assert(self.l[3].get_full_url()=='http://www.rediff.com/sports/2003/jun/25beck1.htm')
        assert(self.l[4].get_full_url()=='http://ftp.gnu.org/pub/lpf.README')
        assert(self.l[5].get_full_url()=='http://www.python.org/doc/2.3b2')
        assert(self.l[6].get_full_url()=='http://images.sourceforge.net/div.png')
        assert(self.l[7].get_full_url()=='http://pyro.sourceforge.net/manual/LICENSE')
        assert(self.l[8].get_full_url()=='http://www.foo.com/bar/python/test.htm')
        assert(self.l[9].get_full_url()=='http://www.foo.com/python/test.css')
        assert(self.l[10].get_full_url()=='http://www.garshol.priv.no/visuals/standard.css')
        assert(self.l[11].get_full_url()=='http://www.fnorb.org/index.html')
        assert(self.l[12].get_full_url()=='http://profigure.sourceforge.net/index.html')
        assert(self.l[13].get_full_url()=='http://www.foo.com/bar/index.html')
        assert(self.l[14].get_full_url()=='http://nltk.sourceforge.net/lite/doc/api/nltk_lite.contrib.fst.draw_graph.GraphEdgeWidget-class.html')
        assert(self.l[15].get_full_url()=='http://www.python.org/doc/current/icons/up.png')
        assert(self.l[16].get_full_url()=='http://www.eidsvoll.kommune.no/eway/eway/library/getmessage.asp?objectid=27015&moduleid=160')
        assert(self.l[17].get_full_url()=='http://www.dz-rs.si/index.php')
        assert(self.l[18].get_full_url()=='http://www.evvs.dk/index.php?cPath=26&osCsid=90207c4908a98db6503c0381b6b7aa70')
        assert(self.l[19].get_full_url()=='http://arstechnica.com/reviews/os/macosx-10.4.ars/')
        assert(self.l[20].get_full_url()=='http://www.fylkesmannen.no/fmt_hoved.asp')
        assert(self.l[21].get_full_url()=='http://www.example.com/display%3C%5D%2F?weight=1.0&article=fred&lang=en&size=100&country=in&q=&id=')
        assert(self.l[22].get_full_url()=='file:extension.css')
        assert(self.l[23].get_full_url()=='file://home/anand/style.css')
        assert(self.l[24].get_full_url()=='file://style.css')
        assert(self.l[25].get_full_url()=='file:/home/anand/style.css')
        assert(self.l[26].get_full_url()=='file:/home/anand')
        assert(self.l[27].get_full_url()=='file://home/anand')
        assert(self.l[28].get_full_url()=='http://www.foo.com/bar/')        

        # Second set
        assert(self.l2[0].get_full_url()=='http://razor.occams.info/code/repo/coderef.c')
        assert(self.l2[1].get_full_url()=='http://razor.occams.info/code/repo/?/govtrack/sec/coderef2.c')
        assert(self.l2[2].get_full_url()=='http://razor.occams.info/code/repo/?/sec/coderef3.c')
        assert(self.l2[3].get_full_url()=='http://razor.occams.info/code/repo/?sec/coderef4.c')
        assert(self.l2[4].get_full_url()=='http://razor.occams.info/code/repo/sec/coderef5.c')
        assert(self.l2[5].get_full_url()=='http://razor.occams.info/sec/coderef6.c')
        assert(self.l2[6].get_full_url()=='http://razor.occams.info/code/repo/govtrack/sec/coderef7.c')
        assert(self.l2[7].get_full_url()=='http://razor.occams.info/code/repo/govtrack/?/sec/../coderef8.c')
        assert(self.l2[8].get_full_url()=='http://www.foo.com/govtrack/sec/?/id/../coderef9.c')
        assert(self.l2[9].get_full_url()=='http://razor.occams.info/code/repo2/govtrack/sec/?/id/../coderef10.c')
        assert(self.l2[10].get_full_url()=='http://razor.occams.info/code/coderef11.c')
        assert(self.l2[11].get_full_url()=='http://razor.occams.info/code/repo/govtrack/?/sec/coderef12.c')
        assert(self.l2[12].get_full_url()=='http://razor.occams.info/code/govtrack2/?/../sec/.././sec/coderef13.c')
        assert(self.l2[13].get_full_url()=='http://razor.occams.info/code/repo/?/govtrack/?/sec/coderef14.c')
        assert(self.l2[14].get_full_url()=='http://razor.occams.info/code/sec/?/../?/./sec/coderef15.c')                
        
        
               
    def test_is_file_like(self):

        assert(self.l[0].filelike==True)
        assert(self.l[1].filelike==True)
        assert(self.l[2].filelike==False)
        assert(self.l[3].filelike==True)
        assert(self.l[4].filelike==True)
        assert(self.l[5].filelike==True)
        assert(self.l[6].filelike==True)
        assert(self.l[7].filelike==True)
        assert(self.l[8].filelike==True)
        assert(self.l[9].filelike==True)
        assert(self.l[10].filelike==True)
        assert(self.l[11].filelike==True)
        assert(self.l[12].filelike==True)
        assert(self.l[13].filelike==True)
        assert(self.l[14].filelike==True)
        assert(self.l[15].filelike==True)
        assert(self.l[16].filelike==True)
        assert(self.l[17].filelike==True)
        assert(self.l[18].filelike==True)
        assert(self.l[19].filelike==False)
        assert(self.l[20].filelike==True)
        assert(self.l[21].filelike==True)                        
        
    def test_anchor_tag(self):

        assert(self.l[0].get_anchor()=='')
        assert(self.l[1].get_anchor()=='')
        assert(self.l[2].get_anchor()=='')
        assert(self.l[3].get_anchor()=='')
        assert(self.l[4].get_anchor()=='')
        assert(self.l[5].get_anchor()=='')
        assert(self.l[6].get_anchor()=='')
        assert(self.l[7].get_anchor()=='')
        assert(self.l[8].get_anchor()=='')
        assert(self.l[9].get_anchor()=='')
        assert(self.l[10].get_anchor()=='')
        assert(self.l[11].get_anchor()=='')
        assert(self.l[12].get_anchor()=='')
        assert(self.l[13].get_anchor()=='#anchor')
        assert(self.l[14].get_anchor()=='#__init__#index-after')
        assert(self.l[15].get_anchor()=='')
        assert(self.l[16].get_anchor()=='')
        assert(self.l[17].get_anchor()=='')
        assert(self.l[18].get_anchor()=='')
        assert(self.l[19].get_anchor()=='')
        assert(self.l[20].get_anchor()=='')
        assert(self.l[21].get_anchor()=='')                        

    def test_canonical_url(self):
        assert(self.l[21].get_canonical_url()=='http://example.com/display%3C%5D%2F?article=fred&country=in&lang=en&size=100&weight=1.0')

def run(result):
    return test_base.run_test(TestHarvestManUrl, result)

if __name__=="__main__":
    s = unittest.makeSuite(TestHarvestManUrl)
    unittest.TextTestRunner(verbosity=2).run(s)
    test_base.clean_up()
    
    
