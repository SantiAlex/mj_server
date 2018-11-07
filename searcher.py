import tornado.web
from tornado import httpclient

import urllib
import re
from bs4 import BeautifulSoup as bs


async def fetch(request):
    # print(request.body)
    http_client = httpclient.AsyncHTTPClient()
    request.headers['User-Agent'] \
        = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'
    print('headers', request.headers)
    try:
        response = await http_client.fetch(request)
        # print(response.body)
        return response.body.decode()
    except Exception as e:
        print("Error: %s" % e)
    else:
        # print(response.body)
        pass


class Search(tornado.web.RequestHandler):
    async def get(self, word):
        url = 'https://www.imeiju.cc/search.php'
        body = urllib.parse.urlencode({'searchword': word})
        request = httpclient.HTTPRequest(url, method='POST',
                                         headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                         body=body)
        html = await fetch(request)
        # ul = re.findall(r'<ul>.*</ul>',html)[0]
        soup = bs(html)
        result_list = soup.find_all('dl', class_='content')
        result = []
        for i in result_list:
            pic_tag = i.find('a', class_='videopic')
            state_tag = i.find('span', class_='score')
            name_tag = i.find('div', class_='head')
            item = {
                'pic': re.findall(r'url\(.+?\)', pic_tag['style'])[0][4:][:-1] if pic_tag else '',
                'state': state_tag.get_text() if state_tag else '',
                'name': name_tag.get_text() if name_tag else '',
                'id': re.findall(r'(?!/Meiju/M)\d+(?=.html)', str(name_tag))[0]
            }
            result.append(item)
        print(result)
        self.write({'list': result})


class Video(tornado.web.RequestHandler):
    async def get(self, number):
        # url = 'https://www.imeiju.cc/Meiju/M' + number + '.html'
        # request = httpclient.HTTPRequest(url)
        # html = await fetch(request)
        # soup = bs(html)
        # url = 'https://www.imeiju.cc/' + soup.find('div', id='playlist').find('li').find('a')['href']
        url = 'https://www.imeiju.cc/Play/' + number + '-0-0.html'
        request = httpclient.HTTPRequest(url)
        html = await fetch(request)
        # print(re.findall(r'VideoInfoList=".+?"', str(html)))
        playlist = re.findall(r'VideoInfoList=".+?"', str(html))[0][15:][:-1]
        lines = playlist.split('$$$')

        index_url = {}
        for line in lines:
            videos = line.split('$$')[1].split('#')
            for video in videos:
                url = video.split('$')[1]
                if url[0:4] == 'http':
                    index = str(videos.index(video) + 1)
                    if index in index_url:
                        index_url[index].append(url)
                    else:
                        index_url[index] = [url]
        self.write({'playlist': index_url})


class Img(tornado.web.RequestHandler):
    def get(self):
        from pymongo import MongoClient
        client = MongoClient('localhost', 27017)
        db = client['pm']['pm']
        data = db.find_one({'code': '916D11F'})['img']
        print(data)
        self.set_header('Content-Type', 'image/jpg')
        self.write(data)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/search/(?P<word>[\s\S]*)", Search),
            (r"/video/(?P<number>[\s\S]*)", Video),
            (r"/test", Img),
        ]
        settings = {
            'static_path': 'app',
            'static_url_prefix': "/app/",
        }
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    app = Application()
    app.listen(18888)
    tornado.ioloop.IOLoop.current().start()
