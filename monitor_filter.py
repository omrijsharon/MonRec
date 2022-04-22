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
from torch.nn import functional as F
import torchvision.models as models
import model
from copy import copy


def shower(queue, monitor):
    model = GradientModel()
    kernel_size_square = model.kernel_size ** 2
    model.eval()
    model.cuda()
    while True:
        msg = queue.get()
        # while queue.qsize() > 4:
        #     queue.get_nowait()
        if (msg=='DONE'):
            break
        img = np.frombuffer(msg.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)[:, :, ::-1]
        filtered_img = model(img)
        filtered_img = filtered_img / kernel_size_square
        filtered_img = (filtered_img * 255).cpu().numpy().astype(np.uint8)
        cv2.imshow("Output", filtered_img)
        k = cv2.waitKey(1)
        if k == 27:  # Esc key to stop
            break


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


class GradientModel(torch.nn.Module):
    def __init__(self):
        super(GradientModel, self).__init__()
        self.kernel_size = 7
        # self.stride = 2
        self.stride = int((self.kernel_size + 1) / 2)
        axis = torch.sin(torch.linspace(-np.pi/2, np.pi/2, self.kernel_size))
        X, Y = torch.meshgrid(axis, axis)
        self.kernel_x = X.unsqueeze(0).unsqueeze(0)
        self.kernel_y = Y.unsqueeze(0).unsqueeze(0)

    def forward(self, x):
        x = cv2.cvtColor(x, cv2.COLOR_BGR2GRAY)
        x = torch.from_numpy(x).float().unsqueeze(0).unsqueeze(0)
        x = 2 * (x / 255) - 1
        x = torch.sqrt(
            F.conv2d(x, self.kernel_x, stride=self.stride, padding=0) ** 2 \
            + F.conv2d(x, self.kernel_y, stride=self.stride, padding=0) ** 2
        )
        return x.squeeze()


if __name__ == '__main__':


    with mss.mss() as sct:
        # Get information of monitor 2
        monitor_number = 1
        mon = sct.monitors[monitor_number]

        # The screen part to capture
        monitor = {
            "top": mon["top"] + 200,  # 100px from the top
            "left": mon["left"] + 200,  # 100px from the left
            "width": int(1280),
            "height": int(720),
            "mon": monitor_number,
        }

        # img_byte = sct.grab(monitor)
        # img = np.frombuffer(img_byte.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)
        # model(img)

        output = "sct-mon{mon}_{top}x{left}_{width}x{height}.png".format(**monitor)

        pqueue = Queue(maxsize=1)
        tqueue = Queue(maxsize=1)
        shower_p = Process(target=shower, args=(pqueue, monitor))
        shower_p.daemon = True
        shower_p.start()

        # infer_p = Process(target=infer, args=(tqueue, mobilenet_v3_small))
        # infer_p.daemon = True
        # infer_p.start()

        # taker(pqueue)
        # while True:
        t0 = time()
        while True:
            img_byte = sct.grab(monitor)
            pqueue.put(img_byte)
            img = np.frombuffer(img_byte.rgb, np.uint8).reshape(monitor["height"], monitor["width"], 3)
            if img.sum() == 0:
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