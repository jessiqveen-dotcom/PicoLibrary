"""
# main.py
# Main application entry point for the Store Customer Feedback System on Raspberry Pi Pico
# Author: jessiqveen-dotcom
"""

import time
from Log import *
from FeedbackController import FeedbackController

# Wait briefly for USB serial to initialize
time.sleep(0.1)
Log.i("Starting Store Customer Feedback System...")

if __name__ == "__main__":
    controller = FeedbackController()
    try:
        controller.run()
    except KeyboardInterrupt:
        Log.i("Stopping Store Customer Feedback System...")
        controller.stop()
