import os
import sys
import argparse
import mss

def capture_screenshot(monitor_number):
    screenshot_path = "./temp/screenshot.png"
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

    with mss.mss() as sct:
        monitor = sct.monitors[monitor_number]
        sct_img = sct.grab(monitor)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=screenshot_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture a screenshot of a monitor.")
    parser.add_argument("monitor_number", type=int, nargs='?', default=1, help="The monitor number to capture (default: 1).")
    args = parser.parse_args()

    capture_screenshot(args.monitor_number)
