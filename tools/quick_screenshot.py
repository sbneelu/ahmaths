import os
import time
import pyautogui
from pynput import mouse

screenshots_dir = "screenshots"
if not os.path.exists(screenshots_dir):
    os.mkdir(screenshots_dir)

time.sleep(5)

class DragListener:
    def __init__(self):
        self.start_pos = None
        self.end_pos = None
        self.dragging = False

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            if pressed:
                self.start_pos = (x, y)
                self.dragging = True
            else:
                self.end_pos = (x, y)
                self.dragging = False

    def on_move(self, x, y):
        if self.dragging:
            self.end_pos = (x, y)

    def on_scroll(self, x, y, dx, dy):
        pass

listener = DragListener()
with mouse.Listener(on_click=listener.on_click, on_move=listener.on_move, on_scroll=listener.on_scroll) as listener:
    while listener.running:
        if listener.start_pos is not None and listener.end_pos is not None:
            x1, y1 = listener.start_pos
            x2, y2 = listener.end_pos
            if x2 == x1 and y2 == y1:
                continue

            # Capture the screen and crop to the selected area
            screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))

            # Save the screenshot to a file with a timestamp
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            screenshot_file = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
            screenshot.save(screenshot_file)

            listener.start_pos = None
            listener.end_pos = None