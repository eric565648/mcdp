import sys
from bs4 import BeautifulSoup
from bs4.element import Tag
from mcdp import logger

def embed_css_files(soup):
    """ Look for <link> elements of CSS and embed them if they are local files"""
    # <link href="..." rel="stylesheet" type="text/css"/>
    for link in list(soup.findAll('link', attrs={'rel':'stylesheet', 'href': True})):
        href = link.attrs['href']
        if href.startswith('/'): # not on windows?
            logger.info('Embedding %r' % href)
            data = open(href).read()
            style = Tag(name='style')
            style.attrs['type'] = 'text/css'
            style.string = data
            link.replace_with(style)
    
    
if __name__ == '__main__':
    sys.stderr.write('Loading from stdin...\n')
    
    contents = sys.stdin.read()
    soup = BeautifulSoup(contents, 'lxml', from_encoding='utf-8')
    embed_css_files(soup)
    contents2 = str(soup)
    sys.stdout.write(contents2)