from multiprocessing import Process, Queue
import numpy as np
from copy import copy
from time import sleep
import zerorpc


class HelloRPC:
    def __init__(self):
        self.counter = 0

    def hello(self, hash_id):
        s = "Hello, {}, you are the {}th process saying hello".format(hash_id, self.counter)
        self.counter += 1
        return s


def run_server():
    s = zerorpc.Server(HelloRPC())
    s.bind("tcp://0.0.0.0:4242")
    print("starting server")
    s.run()


class HelloClient(Process):
    def __init__(self, hash_id):
        super(HelloClient, self).__init__()
        self.hash_id = hash_id

        # self.hash_id = np.random.rand()

    def run(self):
        c = zerorpc.Client()
        c.connect("tcp://127.0.0.1:4242")
        s = c.hello(self.hash_id)
        print(s)

    # def __getstate__(self):
    #     return {"hash": self.hash_id}


if __name__ == '__main__':
    server_p = Process(target=run_server)
    server_p.start()
    # client = HelloClient()
    # client.get_hello("Omri")
    clients_p = [HelloClient(i) for i in range(10)]
    # clients_p = [Process(target=client.get_hello, args=(i,)) for i, client in enumerate(clients)]
    [client_p.start() for client_p in clients_p]
    print("------------------------------------------------------")
    [client_p.join() for client_p in clients_p]