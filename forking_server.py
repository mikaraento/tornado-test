import random
import time

import tornado.gen
import tornado.httpclient
import tornado.httpserver
import tornado.ioloop
import tornado.process
import tornado.web

task_id = -1
http_client = None

def client():
    global http_client
    if not http_client:
        tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
        http_client = tornado.httpclient.AsyncHTTPClient(max_clients=5000)
    return http_client

@tornado.gen.coroutine
def inner():
    yield tornado.gen.Task(tornado.ioloop.IOLoop.instance().add_timeout, time.time() + 0.3)
    raise tornado.gen.Return(1)

fetched = None

def fetch():
    global fetched
    if not fetched:
        fetched = inner()
    return fetched
    
class MainHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        yield fetch()
        self.write("Hello, world\n")
        self.finish()

class ForwardingHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        url = "http://127.0.0.1:%d/" % (random.randrange(8001, 8005))
        response = yield client().fetch(url)
        self.write(response.body)
        self.finish()

MASTER_TASKS = 7

def child():
    application = tornado.web.Application([
        (r"/", MainHandler),
    ])
    application.listen(8001 + task_id - MASTER_TASKS)
    tornado.ioloop.IOLoop.instance().start()

def master(sockets):
    application = tornado.web.Application([
        (r"/", ForwardingHandler),
    ])
    server = tornado.httpserver.HTTPServer(application)
    server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    sockets = tornado.netutil.bind_sockets(8000)
    task_id = tornado.process.fork_processes(MASTER_TASKS + 4)
    if task_id < MASTER_TASKS:
        #import cProfile
        #pr = cProfile.Profile()
        #pr.enable()
        try:
            master(sockets)
        except KeyboardInterrupt, e:
            #pr.dump_stats("profile")
            pass
    else:
        child()
