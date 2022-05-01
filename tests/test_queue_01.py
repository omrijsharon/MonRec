from multiprocessing import Process, Queue
# from queue import Queue
from time import sleep


def get_from_queue(name, q: Queue):
    while not q.empty():
        print("\n {} : {}, is empty: {}".format(name, q.get(), q.empty()))
        sleep(0.1)


q = Queue()
for i in range(100):
    q.put(i)


def set_daemon_true(p):
    p.daemon = True

if __name__ == '__main__':
    p = [Process(target=get_from_queue, args=(i, q)) for i in range(10)]
    [set_daemon_true(pp) for pp in p]
    [pp.start() for pp in p]
    [pp.join() for pp in p]
    print("done")