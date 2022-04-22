import pygame
import numpy as np
import matplotlib.pyplot as plt
from drawnow import drawnow


fps = 20
past = 5
pygame.init()


def make_fig():

    plt.subplot(1, 2, 1)
    plt.scatter(x[:, 0], x[:, 1], lw=0, alpha=np.linspace(0.1, 1, past))
    plt.axis('square')
    plt.xlim(-1, 1)
    plt.ylim(-1, 1)
    plt.subplot(1, 2, 2)
    plt.scatter(x[:, 2], x[:, 3], lw=0, alpha=np.linspace(0.1, 1, past))
    plt.axis('square')
    plt.xlim(-1, 1)
    plt.ylim(-1, 1)


def mapFromTo(x, a, b, c, d):
    y = (x - a) / (b - a) * (d - c) + c
    return y


pygame.display.set_caption('JoyStick Example')
surface = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
running = True

font = pygame.font.Font(None, 20)
linesize = font.get_linesize()
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
for joy in joysticks:
    joy.init()

x = np.zeros(shape=(1, 4))
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # surface.fill((0, 0, 0))

    # joystick buttons
    x = np.vstack((x, np.array([joysticks[0].get_axis(i) for i in range(4)]).reshape(1,-1)))
    x = x[-past:]
    drawnow(make_fig)
    # print(["Joystick {}, Axis {} value ".format(j, ) for i in range(joysticks[j].get_numaxes())])

    pygame.display.flip()
    clock.tick(fps)

pygame.quit()