#!/usr/bin/env python

import time
from datetime import timedelta
from bs4 import BeautifulSoup as bs
import re
import urllib

try:
    from HTMLParser import HTMLParser
    from urlparse import urljoin, urldefrag
except ImportError:
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urldefrag

from tornado import httpclient, gen, ioloop, queues

base_url = 'http://www.tornadoweb.org/en/stable/'
concurrency = 10


@gen.coroutine
def get_links_from_url(url):
    """Download the page at `url` and parse it for links.

    Returned links have had the fragment after `#` removed, and have been made
    absolute so, e.g. the URL 'gen.html#tornado.gen.coroutine' becomes
    'http://www.tornadoweb.org/en/stable/gen.html'.
    """
    try:
        response = yield httpclient.AsyncHTTPClient().fetch(url)
        print('fetched %s' % url)

        html = response.body if isinstance(response.body, str) \
            else response.body.decode(errors='ignore')
        urls = [urljoin(url, remove_fragment(new_url))
                for new_url in get_links(html)]
    except Exception as e:
        print('Exception: %s %s' % (e, url))
        raise gen.Return([])

    raise gen.Return(urls)


async def get_html(url):
    try:
        response = await httpclient.AsyncHTTPClient().fetch(url, request_timeout=0.2)
    finally:
        if response.code and response.code == 200:
            return response
        else:
            print('asd')


async def get_update_list_by_index(index):
    url = 'http://www.kanmeiju.net/index.php?s=video/search/p/' + str(index) + '.html'
    request = httpclient.HTTPRequest(url, headers={'Cookie': 'PHPSESSID=ugbrbcgpv1kc29oc740r10lmn0'}, request_timeout=2)
    # response = await httpclient.AsyncHTTPClient().fetch(request)
    response = await get_html(url)
    print(response.headers)
    html = response.body if isinstance(response.body, str) \
        else response.body.decode(errors='ignore')
    print(url)
    parse_html = bs(html, 'lxml')
    update_list = parse_html.find('div', class_='listri').find('ul').find_all('li')
    for i in update_list:
        p = i.find_all('p')
        # print(p[0].string)
        # print(p[3].find('font').string)
        # print(re.findall(r'detail/.+\.html',str(p[0]))[0][7:][:-5])
    return 1
    # return parse_html.find('div', class_='listri').find_all('li ')


def read_update_list(update_list):
    pass


def remove_fragment(url):
    pure_url, frag = urldefrag(url)
    return pure_url


def get_links(html):
    class URLSeeker(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.urls = []

        def handle_starttag(self, tag, attrs):
            href = dict(attrs).get('href')
            if href and tag == 'a':
                self.urls.append(href)

    url_seeker = URLSeeker()
    url_seeker.feed(html)
    return url_seeker.urls


def search(word):
    url = 'https://www.imeiju.cc/search.php'
    # body = {
    #     'searchword': urllib.parse.quote(word, safe='/', encoding=None, errors=None)
    # }
    body = urllib.parse.urlencode({'searchword':word})
    request = httpclient.HTTPRequest(url, method='POST', body=body)
    client = httpclient.HTTPClient()
    response = client.fetch(request)
    print(response.body)


# @gen.coroutine
async def main():
    search('美国恐怖')

    i = 1
    # while 1:
    #     print(i)
    #
    #     c = await get_update_list_by_index(i)
    #     i = i + 1

        # if c:
        #     continue
        # q = queues.Queue()
        # start = time.time()
        # fetching, fetched = set(), set()
        #
        # @gen.coroutine
        # def fetch_url():
        #     current_url = yield q.get()
        #     try:
        #         if current_url in fetching:
        #             return
        #
        #         print('fetching %s' % current_url)
        #         fetching.add(current_url)
        #         urls = yield get_links_from_url(current_url)
        #         fetched.add(current_url)
        #
        #         for new_url in urls:
        #             # Only follow links beneath the base URL
        #             if new_url.startswith(base_url):
        #                 yield q.put(new_url)
        #
        #     finally:
        #         q.task_done()
        #
        # @gen.coroutine
        # def worker():
        #     while True:
        #         yield fetch_url()
        #
        # q.put(base_url)
        #
        # # Start workers, then wait for the work queue to be empty.
        # for _ in range(concurrency):
        #     worker()
        # yield q.join(timeout=timedelta(seconds=300))
        # assert fetching == fetched
        # print('Done in %d seconds, fetched %s URLs.' % (
        #     time.time() - start, len(fetched)))


if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
