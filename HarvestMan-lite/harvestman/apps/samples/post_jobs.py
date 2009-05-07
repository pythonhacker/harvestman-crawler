#!/usr/bin/env python
import sys
import blogger
import getpass
import cPickle

def post_jobs(*fnames):
    print 'About to post jobs from %d dumps' % len(fnames)
    print 'Logging to blogger...'

    username = raw_input("Enter username: ").strip()
    passwd = getpass.getpass("Enter password: ").strip()
    b = blogger.BlogJobPoster(username, passwd)
    print 'Successfully logged into blogger.'
    
    for fname in fnames:
        print 'Posting job from file %s' % fname
        jobs = cPickle.load(open(fname,'rb'))
        print 'Found %d job postings' % len(jobs)

        count = 0
        content = ''

        for title, (url,data) in jobs.items():
            # Extract date from the text...
            print data
            go_ahead = raw_input("Post this JOB [y/n] ? ")
            if go_ahead.lower().strip() != 'y': continue

            count += 1
            date = data[data.find('<I>')+3:data.find('</I>')]
            title += '(Posted on: %s)' % date
            content = data[data.find('<PRE>')+5:data.find('</PRE>')] + '<br>\n'
            # Wrap content to text width nicely
            # content = wrap(content) + '<br>'

            content += 'Referrering URL: <i><a href="%s">%s</a></i>\n' % (url, url)
            content = '<P>' + content + '</P>'

            print 'Posting job ID %d for %s' % (count, url)
            b.post_job(title, content)

if __name__ == "__main__":
    post_jobs(*sys.argv[1:])
