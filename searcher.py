import tornado.web
from tornado import httpclient

import urllib
import re
from bs4 import BeautifulSoup as bs


async def fetch(request):
    print(request.body)
    http_client = httpclient.AsyncHTTPClient()
    try:
        response = await http_client.fetch(request)
    except Exception as e:
        print("Error: %s" % e)
    else:
        print(response.body)
        return response.body.decode()


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
        url = 'https://www.imeiju.cc/Meiju/M' + number + '.html'
        request = httpclient.HTTPRequest(url)
        html = await fetch(request)
        soup = bs(html)
        url = 'https://www.imeiju.cc/' + soup.find('div', id='playlist').find('li').find('a')['href']
        request = httpclient.HTTPRequest(url)
        html = await fetch(request)
        playlist = re.findall(r'VideoInfoList=".+?"', str(html))[0][15:][:-1]
        lines = playlist.split('$$$')
        for line in lines:
            # server = i.split('$$')[0]
            videos = line.split('$$')[1].split('#')
            for video in videos:
                url = video.split('$')[1]
                print(url)
        self.write({'playlist': playlist})


def make_app():
    return tornado.web.Application([
        (r"/search/(?P<word>[\s\S]*)", Search),
        (r"/video/(?P<number>[\s\S]*)", Video),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(18888)
    tornado.ioloop.IOLoop.current().start()
