import argparse
from core.record import start_recording

parser = argparse.ArgumentParser()

parser.add_argument('--path', type=str, default="", required=False, help="path for saving recordings.")
parser.add_argument('--monitor_number', type=int, default=1, required=False, help="Monitor number to record from.")
parser.add_argument('--game', type=str, default='liftoff', required=False, help="Choose a game to record: liftoff, uncrashed, velocidrone, drl.")
parser.add_argument('--png_compression', type=int, default=6, required=False, help="PNG compression.")

args = parser.parse_args()


def main():
    start_recording(args)


if __name__ == '__main__':
    main()