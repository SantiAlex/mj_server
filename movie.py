import tornado
from tornado import web, options, httpclient
import re

sub_path = 'xiguamovie'


class LogHandler(web.RequestHandler):
    async def get(self, uri):
        # print(uri)
        url = 'http://m.ukohxt.cn' + uri.replace(sub_path, '')
        # print(url)
        request = httpclient.HTTPRequest(url, connect_timeout=60, request_timeout=60)
        client = httpclient.AsyncHTTPClient()
        response = await client.fetch(request)
        if 'text/html' in response.headers['Content-Type']:
            pattern = re.compile(r'<script>[\s\S]+?</script>')
            data = re.sub(pattern, '', response.body.decode())
            pattern = re.compile(r'<script type="text/javascript">[\s\S]+?</script>')
            data = re.sub(pattern, '', data)
            pattern = re.compile(r'<a id="gzwx">[\s\S]+?</a>')
            data = re.sub(pattern, '', data)
            data = data.replace('overflow: hidden', "")
            data = data.replace('href="/', 'href="' + '/' + sub_path + '/')
            data = data.replace('src="/', 'src="' + '/' + sub_path + '/')
            data = data.replace('/index.php/search', '/' + sub_path + '/index.php/search')
            data = data.replace('请发送邮箱值xiakai920@gmail.com，', '')


        else:
            data = response.body
        self.write(data)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/(?P<uri>.*)', LogHandler),

        ]

        settings = {
        }

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.options.parse_command_line()

    app = Application()
    server = tornado.httpserver.HTTPServer(app, xheaders=True, max_buffer_size=10000000000)
    server.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
