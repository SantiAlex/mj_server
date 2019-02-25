from bs4 import BeautifulSoup as bs
import requests
import time

from tornado import httpclient, gen, ioloop, queues
from pymongo import MongoClient

mongo_client = MongoClient('192.168.0.21', 27017)
db = mongo_client['pm']['pm']
conf = mongo_client['pm']['conf']


def get_html(url):
    try:
        r = requests.get(url)
        return r.text
    except Exception as e:
        print(e)


def get_img():
    url = 'https://cdn4.thumbs.motherlessmedia.com/thumbs/916D11F-strip.jpg'
    r = httpclient.HTTPClient().fetch(url)
    print(len(r.body), type(r.body))
    db.update({'code': '916D11F'}, {'$set': {'img': r.body}}, True)


async def async_get_html(url):
    print(url)
    try:
        t = time.time()
        client = httpclient.AsyncHTTPClient()
        request = httpclient.HTTPRequest(url, follow_redirects=False)
        r = await client.fetch(request)
        print(r.code, url, time.time() - t)
    finally:
        if r.code == 200:
            return r.body
        else:
            raise


def parse_html(html):
    soup = bs(html)
    div_list = soup.find_all('div', class_='thumb video medium')
    for i in div_list:
        code = i.get('data-codename')
        name = i.h2.text
        long = i.div.div.text.split(':')
        if len(long) == 2:
            long = int(long[0]) * 60 + int(long[1])
        elif len(long) == 3:
            long = int(long[0]) * 3600 + int(long[1]) * 60 + int(long[2])
        # print(code, name, long)
        data = {
            'code': code,
            'name': name,
            'long': long
        }
        db.update({'code': code}, {'$setOnInsert': data}, True)


class IndexMaker(object):
    def __init__(self):
        config = conf.find_one()
        if not config:
            config = {
                'index': 0,
                'working_pool': [],
                'returned_pool': []
            }
            conf.insert(config)
        self.index = config['index']
        self.returned_index_pool = set(config['returned_pool'])
        self.returned_index_pool.update(set(config['working_pool']))
        self.working_index_pool = set()

    def get_index(self):
        if self.returned_index_pool:
            i = self.returned_index_pool.pop()
            self.working_index_pool.add(i)
            conf.update({}, {'$set': {'returned_pool': list(self.returned_index_pool),
                                      'working_pool': list(self.working_index_pool)}})
            return i
        else:
            index = self.index
            self.index += 60
            self.working_index_pool.add(index)
            conf.update({}, {'$set': {'index': self.index,
                                      'working_pool': list(self.working_index_pool)}})
            return index

    def returned_index(self, index):
        self.returned_index_pool.add(index)
        self.working_index_pool.remove(index)
        conf.update({}, {'$set': {'returned_pool': list(self.returned_index_pool),
                                  'working_pool': list(self.working_index_pool)}})

    def finished_index(self, index):
        self.working_index_pool.remove(index)
        conf.update({}, {'$set': {'working_pool': list(self.working_index_pool)}})


async def main():
    im = IndexMaker()

    # for i in range(10):
    #     print(im.get_index())
    #     time.sleep(1)

    # get_img()

    # url = 'https://motherless.com/videos/archives?i=1'
    # t = time.time()
    # parse_html(get_html(url))
    # print(time.time() - t)
    #
    # q = queues.Queue()

    # for i in range(10):
    #
    #     while True:
    #         url = 'https://motherless.com/videos/archives?i=' + str(im.get_index())
    #         await async_get_html(url)
    #     q.put(url)
    # while 1:
    #     async for url in q:
    #         ioloop.IOLoop.current().spawn_callback(async_get_html, url)
    # await async_get_html(url)

    async def worker():
        while True:
            index = im.get_index()
            try:
                url = 'https://motherless.com/videos/archives?i=' + str(index)
                parse_html(await async_get_html(url))
                im.finished_index(index)
            except:
                im.returned_index(index)

    workers = gen.multi([worker() for _ in range(3)])
    await workers


async def img_main():
    cursor = db.find({'long': {'$gt': 1459, '$lt': 2460}, 'img': None}, {'code': 1})
    code_list = []
    for i in cursor:
        code_list.append(i['code'])

    async def worker():
        while code_list:
            code = code_list.pop()

            url = 'https://cdn4.thumbs.motherlessmedia.com/thumbs/' + code + '-strip.jpg'
            request = httpclient.HTTPRequest(url, follow_redirects=False)
            r = await httpclient.AsyncHTTPClient().fetch(request)
            if r.code == 200:
                db.update({'code': code}, {'$set': {'img': r.body}}, True)
                print(code)
            else:
                print('=================: ', code)

    workers = gen.multi([worker() for _ in range(60)])
    await workers


if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(img_main)
