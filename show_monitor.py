import numpy as np
from time import sleep, time
import mss
import mss.tools
import cv2
from multiprocessing import Process, Queue


def shower(queue, monitor):
    while True:
        msg = queue.get()
        # while queue.qsize() > 4:
        #     queue.get_nowait()
        if (msg=='DONE'):
            break
        cv2.imshow("Output", np.fromstring(msg.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1])
        k = cv2.waitKey(1)
        if k == 27:  # Esc key to stop
            break


def taker(queue):
    # while True:
    for ii in range(1000):
        queue.put(sct.grab(monitor))
    queue.put('DONE')


if __name__ == '__main__':
    with mss.mss() as sct:
        # Get information of monitor 2
        monitor_number = 1
        mon = sct.monitors[monitor_number]

        # The screen part to capture
        monitor = {
            "top": mon["top"] + 150,  # 100px from the top
            "left": mon["left"] + 300,  # 100px from the left
            "width": 1280,
            "height": 720,
            "mon": monitor_number,
        }
        output = "sct-mon{mon}_{top}x{left}_{width}x{height}.png".format(**monitor)

        pqueue = Queue(maxsize=1)
        shower_p = Process(target=shower, args=(pqueue,monitor))
        shower_p.daemon = True
        shower_p.start()

        # taker(pqueue)
        # while True:
        for ii in range(10000):
            pqueue.put(sct.grab(monitor))
        pqueue.put('DONE')
        shower_p.join()

        # Grab the data
        # while True:
        #     sct_img = sct.grab(monitor)
        #     rgb_img = np.fromstring(sct_img.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1]
        #     cv2.imshow("Output", rgb_img)
        #     k = cv2.waitKey(1)
        #     if k == 27:  # Esc key to stop
        #         break

        # Save to the picture file
        # mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
        # print(output)