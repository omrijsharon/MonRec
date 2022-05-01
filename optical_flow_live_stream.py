import numpy as np
from time import sleep, time
import mss
import mss.tools
import cv2
# from multiprocessing import Process, Queue
from torch.multiprocessing import Process, Queue
from drawnow import drawnow
import matplotlib.pyplot as plt
import torch
import torchvision.models as models
import model
from copy import copy


def shower(queue, monitor):
    # params for ShiTomasi corner detection
    feature_params = dict(maxCorners=100,
                          qualityLevel=0.01,
                          minDistance=5,
                          blockSize=7)
    lk_params = dict(winSize=(10, 10),
                     maxLevel=3,
                     criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
    color = np.random.randint(0, 255, (100, 3))
    msg = queue.get()
    old_frame = np.frombuffer(msg.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)
    old_frame = cv2.cvtColor(old_frame, cv2.COLOR_RGB2BGR)
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)

    # mask = np.zeros(shape=(int(640*1.5), int(480*1.5), 3), dtype=np.uint8)
    mask = np.zeros_like(old_frame)
    while True:
        msg = queue.get()
        # while queue.qsize() > 4:
        #     queue.get_nowait()
        if (msg=='DONE'):
            break
        # frame = np.frombuffer(msg.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1]
        frame = np.frombuffer(msg.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

        if p1 is None or len(p1) < 6:
            p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
            img = cv2.add(frame, mask*0)
            continue

        # Select good points
        good_new = p1[st == 1]
        good_old = p0[st == 1]

        for i, (new, old) in enumerate(zip(good_new, good_old)):
            a, b = new.ravel().astype(int)
            c, d = old.ravel().astype(int)
            # mask = cv2.line(mask, (a, b), (c, d), color[i].tolist(), 2)
            frame = cv2.circle(frame, (a, b), 5, color[i].tolist(), -1)
        img = cv2.add(frame, mask)

        cv2.imshow("Output", img)
        k = cv2.waitKey(1)
        if k == 27:  # Esc key to stop
            break

        old_gray = frame_gray.copy()
        p0 = good_new.reshape(-1, 1, 2)

    cv2.destroyAllWindows()


def shower_plain(queue, monitor):
    while True:
        msg = queue.get()
        # while queue.qsize() > 4:
        #     queue.get_nowait()
        if (msg=='DONE'):
            break
        # frame = np.frombuffer(msg.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1]
        frame = np.frombuffer(msg.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Output", frame)
        k = cv2.waitKey(1)
        if k == 27:  # Esc key to stop
            break
    cv2.destroyAllWindows()

def infer(torch_queue, nn_model):
    def make_fig():
        print(y)
        plt.scatter(y[0], y[1])
        plt.xlim(-1, 1)
        plt.ylim(-1, 1)
    while True:
        img = torch_queue.get()
        x = torch.from_numpy(img.transpose((2, 0, 1))).float()
        x = model.normalize(x.unsqueeze(dim=0).requires_grad_(False))
        y = nn_model(x)
        # print(torch.argmax(y[0]))
        y = y.numpy().reshape(-1)
        drawnow(make_fig)


def taker(queue):
    # while True:
    for ii in range(1000):
        queue.put(sct.grab(monitor))
    queue.put('DONE')


if __name__ == '__main__':
    basic_model = models.mobilenet_v3_small(pretrained=True)
    # basic_model.eval()
    # mobilenet_v3_small = model.Model(basic_model, 2).requires_grad_(False)
    # mobilenet_v3_small.eval()
    # mobilenet_v3_small.cuda()

    with mss.mss() as sct:
        # Get information of monitor 2
        monitor_number = 1
        mon = sct.monitors[monitor_number]

        # The screen part to capture
        monitor = {
            "top": mon["top"] + 160,  # 100px from the top
            "left": mon["left"] + 250,  # 100px from the left
            # "width": int(480*1.5),
            # "height": int(640*1.5),
            "width": int(1280),
            "height": int(720),
            "mon": monitor_number,
        }
        output = "sct-mon{mon}_{top}x{left}_{width}x{height}.png".format(**monitor)

        pqueue = Queue(maxsize=1)
        tqueue = Queue(maxsize=1)
        shower_p = Process(target=shower_plain, args=(pqueue, monitor))
        shower_p.daemon = True
        shower_p.start()

        # infer_p = Process(target=infer, args=(tqueue, mobilenet_v3_small))
        # infer_p.daemon = True
        # infer_p.start()

        # taker(pqueue)
        # while True:
        t0 = time()
        i=0
        while True:
            img_byte = sct.grab(monitor)
            pqueue.put(img_byte)
            img = np.frombuffer(img_byte.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)
            # if img.sum() == 0:
            #     break
            i+=1
            if i==10000:
                break
            # print("capture: ", 1/(time()-t0))
            # t0 = time()
            # x = torch.from_numpy(copy(img.transpose((2, 0, 1)))).float().cuda()
            # x = model.normalize(x.unsqueeze(dim=0).requires_grad_(False))
            # y = mobilenet_v3_small(x)
            # print("infer: ", 1 / (time() - t0))
        pqueue.put('DONE')
        shower_p.join()
        # infer_p.join()

        # Grab the data
        # while True:
        #     sct_img = sct.grab(monitor)
        #     rgb_img = np.frombuffer(sct_img.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1]
        #     cv2.imshow("Output", rgb_img)
        #     k = cv2.waitKey(1)
        #     if k == 27:  # Esc key to stop
        #         break

        # Save to the picture file
        # mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
        # print(output)