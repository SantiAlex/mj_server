from bs4 import BeautifulSoup as bs
import requests

from tornado import httpclient, gen, ioloop


def get_html(url):
    try:
        r = requests.get(url)
        return r.text
    except e:
        print(e)


async def async_get_html(url):
    print(url)
    client = httpclient.AsyncHTTPClient()
    r = await client.fetch(url)
    print(r.code)


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


async def main():
    # url = 'https://motherless.com/videos/archives?i=2999999'
    # parse_html(get_html(url))
    for i in range(20):
        url = 'https://motherless.com/videos/archives?i=' + str(i)

        await async_get_html(url)


if __name__ == '__main__':
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
