import tornado
from tornado import web, options


class Player(web.RequestHandler):
    def get(self, uri):
        print(uri)

        html1 = '''
       <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<video id="video" style="width:300px"></video>
<script>
  if(Hls.isSupported()) {
    var video = document.getElementById('video');
    var hls = new Hls();
    hls.loadSource(' '''

        html2 = ''' ');
            hls.attachMedia(video);
            hls.on(Hls.Events.MANIFEST_PARSED,function() {
              video.play();
          });
         }
        </script> 
            '''
        self.write(html1 + uri + html2)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/player/(?P<uri>.*)', Player),

        ]

        settings = {
        }

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    tornado.options.parse_command_line()

    app = Application()
    server = tornado.httpserver.HTTPServer(app, xheaders=True, max_buffer_size=10000000000)
    server.listen(8001)
    tornado.ioloop.IOLoop.instance().start()
