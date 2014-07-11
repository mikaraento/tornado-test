import json, sys, time
from MySQLdb import connect, cursors
from tornado import gen, httpclient, web, netutil, process, httpserver, ioloop

class BackendHandler(web.RequestHandler):   
    def get(self):
        time.sleep(1)  # simulate longer query
        cur = connect(db='tornado', user='root').cursor(cursors.DictCursor)
        cur.execute("SELECT * FROM foo")
        self.write(json.dumps(list(cur.fetchall())))

class FrontendHandler(web.RequestHandler):
    @gen.coroutine
    def get(self):
        http_client = httpclient.AsyncHTTPClient(max_clients=500)
        response = yield http_client.fetch("http://localhost:8001/foo")
        self.set_header("Content-Type", 'application/json')
        self.write(response.body)


if __name__ == "__main__":
    number_of_be_tasks = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    number_of_fe_tasks = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    fe_sockets = netutil.bind_sockets(8000)  # need to bind sockets
    be_sockets = netutil.bind_sockets(8001)  # before forking
    task_id = process.fork_processes(number_of_be_tasks + number_of_fe_tasks)
    if task_id < number_of_fe_tasks:
        handler_class = FrontendHandler
        sockets = fe_sockets
    else:
        handler_class = BackendHandler
        sockets = be_sockets
    httpserver.HTTPServer(web.Application([(r"/foo", handler_class)])
        ).add_sockets(sockets)
    ioloop.IOLoop.instance().start()
