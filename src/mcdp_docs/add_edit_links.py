from mcdp import logger
import sys

from bs4 import BeautifulSoup
from bs4.element import Tag


def add_github_links_if_edit_url(soup):
    """ If an element has an attribute 'github-edit-url' then add little icons """
    attname = 'github-edit-url'
    nfound = 0
    for h in soup.findAll(['h1','h2','h3','h4'], attrs={attname: True}):
        nfound += 1
        a = Tag(name='a')
        a.attrs['href'] = h.attrs[attname]
        a.attrs['class'] = 'github-edit-link'
        a.string = ' ✎'
        h.append(a)
#         msg = 'Found element %s' % h
#         logger.info(msg)
    
    logger.info('Found %d elements with attribute %r' % (nfound, attname) )
        
        
if __name__ == '__main__':
    sys.stderr.write('Loading from stdin...\n')
    
    contents = sys.stdin.read()
#     print ('start: %s  ... %s' % (contents[:100], contents[-100:]))
    soup = BeautifulSoup(contents, 'lxml', from_encoding='utf-8')
#     soup = bs(contents)
#     print 'soup: %s' % soup
    ssoup = str(soup)
#     print ('\n\nstart: %s  ... %s' % (ssoup[:100], ssoup[-100:]))
    
    add_github_links_if_edit_url(soup)
#     print(str(soup)[:0])
    
    contents2 = str(soup)
    sys.stdout.write(contents2)