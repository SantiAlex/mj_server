from bs4 import BeautifulSoup as bs
import requests
import time

from tornado import httpclient, gen, ioloop, queues
from pymongo import MongoClient

mongo_client = MongoClient('localhost', 27017)
db = mongo_client['pm']['pm']

def get_html(url):
    try:
        r = requests.get(url)
        return r.text
    except Exception as e:
        print(e)


async def async_get_html(url):
    print(url)
    t = time.time()
    client = httpclient.AsyncHTTPClient()
    r = await client.fetch(url)
    print(r.code, url, time.time() - t)


def parse_html(html):
    soup = bs(html)
    l = soup.find_all('div', class_='thumb video medium')
    for i in l:
        code = i.get('data-codename')
        name = i.h2.text
        long = i.div.div.text.split(':')
        if len(long) == 2:
            long = int(long[0]) * 60 + int(long[1])
        elif len(long) == 3:
            long = int(long[0]) * 3600 + int(long[1]) * 60 + int(long[2])
        print(code, name, long)
        data = {
            'code': code,
            'name': name,
            'long': long
        }
        db.insert(data)


async def main():
    url = 'https://motherless.com/videos/archives?i=1'
    t = time.time()
    parse_html(get_html(url))
    print(time.time() - t)

    q = queues.Queue()

    for i in range(10):
        # url = 'https://motherless.com/videos/archives?i=' + str(i)
        url = 'https://www.baidu.com?i=' + str(i)
        q.put(url)
    while 1:
        async for url in q:
            ioloop.IOLoop.current().spawn_callback(async_get_html, url)
    await async_get_html(url)


if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
