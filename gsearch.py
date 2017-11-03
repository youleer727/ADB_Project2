# reference: Google custom search API client implementations
# link: https://github.com/google/google-api-python-client/blob/master/samples/customsearch/main.py
# author: jcgregorio@google.com (Joe Gregorio)
import json
import urllib
from googleapiclient.discovery import build

import tika
tika.initVM()
from tika import parser

"""Search Document class

a document returned by Google search engine, extracted from the 'item' part 
of the JSON data returned by Google search API, including information such as 
the title, URL link, and a snippet of document. Most importantly, the pure 
texts of the webpage are extracted for external use
"""
class SearchDocument(object):
    ## the constructor
    #  @param fields "items" of Google search results, type: dict
    def __init__(self, fields):
        self.title = fields['title']
        self.displink = fields['displayLink']
        self.url = fields['link'] # 'link' is the complete URL, not 'formattedUrl'
        self.snippet = fields['snippet']
        self.key = self.url
        self.text = self.scrape(self.url)

    ## scraping text contents from given URL
    #  @param url URL to visit, type: str
    #  @return text contents, type: str
    def scrape(self, url):
        if not url: return ""
        # scrape by retrieving the HTML
        try:
            page = urllib.urlopen(url).read()
        except Exception as e:
            print "failed to open URL, {}".format(e)
            return ""
        
        # calling Apache Tika to extract texts from HTML
        # https://github.com/chrismattmann/tika-python
        contents = parser.from_buffer(page)['content']
        if not contents:
            return ""
        contents = u'\n'.join([c for c in contents.split('\n') if len(c) and not c.isspace()]).encode('ascii', 'ignore')
        
        return contents

## execute search and get the JSON formatted result
#  @param api the Google search API key, type: str
#  @param engine the Google search engine ID, type: str
#  @return type: dict
def gsearch_exec(query, api, engine):
    # Build a service object for interacting with the API. Visit
    # the Google APIs Console <http://code.google.com/apis/console>
    # to get an API key for your own application.
    service = build("customsearch", "v1", developerKey=api)
    return service.cse().list(q=query, cx=engine).execute()

## apply Google search
#  @param query query terms, type: str
#  @param api the Google search API key, type: str
#  @param engine the Google search engine ID, type: str
#  @return list of returned documents, type: list[SearchDocument]
def gsearch(query, api, engine):
    if not query:
        return []
    raw = gsearch_exec(query, api, engine)
    return [SearchDocument(i) for i in raw['items']]
