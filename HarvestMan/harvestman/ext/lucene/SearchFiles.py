# -- coding: utf-8
#!/usr/bin/env python
from PyLucene import QueryParser, IndexSearcher, StandardAnalyzer, FSDirectory
from PyLucene import VERSION, LUCENE_VERSION

"""
This script is loosely based on the Lucene (java implementation) demo class 
org.apache.lucene.demo.SearchFiles.  It will prompt for a search query, then it
will search the Lucene index in the current directory called 'index' for the
search query entered against the 'contents' field.  It will then display the
'path' and 'name' fields for each of the hits it finds in the index.  Note that
search.close() is currently commented out because it causes a stack overflow in
some cases.
"""
def run(searcher, analyzer):

    while True:
        print
        print "Hit enter with no input to quit."
        command = raw_input("Query:")
        if command == '':
            return

        print
        print "Searching for:", command
        query = QueryParser("contents", analyzer).parse(command)
        hits = searcher.search(query)
        print "%s total matching documents" % hits.length()
        
        for i, doc in hits:
            print 'path:', doc.get("path"), 'name:', doc.get("name"), 100*hits.score(i)

if __name__ == '__main__':
    STORE_DIR = "index"
    print 'PyLucene', VERSION, 'Lucene', LUCENE_VERSION
    directory = FSDirectory.getDirectory(STORE_DIR, False)
    searcher = IndexSearcher(directory)
    analyzer = StandardAnalyzer()
    run(searcher, analyzer)
    searcher.close()
