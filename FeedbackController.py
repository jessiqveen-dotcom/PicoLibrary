"""
# FeedbackController.py
# Complete Controller for Satisfaction Kiosk State Model
# Author: jessiqveen-dotcom
"""

import time
from Log import *
from StateModel import StateModel
from Counters import SoftwareTimer
from Button import Button
from Lights import GREEN, RED, YELLOW, BLUE, BLACK
from LightStrip import LightStrip
from Displays import LCDDisplay
from Sensors import UltrasonicSensor
from FeedbackStats import FeedbackStats


class FeedbackController:
    """
    **FeedbackController** implements the 5-state customer satisfaction kiosk state model:
    - **State 0 (Welcome)**: Displays *"Welcome to Kiosk"* and current satisfaction rate.
    - **State 1 (Selection)**: Displays *"Rate your visit: / <3 Green  >2 Red"* and starts a 5-second timer.
    - **State 2 (Happy)**: Records happy feedback, displays *"Thank you"*, plays happy music, and starts a 5-second timer.
    - **State 3 (Unhappy)**: Records unhappy feedback, displays *"Sorry to hear / Feedback noted"*, plays a sad tone, starts a 5-second timer, or transitions to Alarm if below threshold.
    - **State 4 (Alarm)**: Displays *"Call Manager"*, plays a 2-tone alarm in `stateDo`, and resets statistics on exit when `green_press` occurs.

    Parameters:
    ----------
    None

    Examples:
    ---------
    1. Instantiate and run the kiosk controller:
       `controller = FeedbackController()`
       `controller.run()`
    2. Stop the controller cleanly:
       `controller.stop()`
    """

    def __init__(self):
        Log.i("FeedbackController: initializing kiosk controller")

        # 1. Instantiate Business Model
        self._stats = FeedbackStats()
        self._threshold_pct = 30.0

        # 2. Instantiate Hardware Peripherals
        self._display = LCDDisplay(sda=0, scl=1)
        self._lightstrip = LightStrip(pin=2, name="KioskStrip", numleds=8, brightness=0.5)

        try:
            from Buzzer import PassiveBuzzer
            self._buzzer = PassiveBuzzer(pin=16, name="KioskBuzzer")
        except ImportError:
            from Buzzer import ActiveBuzzer
            self._buzzer = ActiveBuzzer(pin=16, name="KioskBuzzer")

        # Buttons: Green (GP18) for Happy/Reset, Red (GP19) for Unhappy
        self._btn_green = Button(18, "green", handler=None, lowActive=True)
        self._btn_red = Button(19, "red", handler=None, lowActive=True)

        # Ultrasonic Sensor: Trigger on GP14, Echo on GP15 (detects within 10cm)
        self._uss = UltrasonicSensor(trigger=14, echo=15, name="uss", threshold=100.0)

        # Software Timer
        self._timer_timeout = SoftwareTimer(name="timer", handler=None)

        # 3. Instantiate StateModel (5 States: 0-Welcome, 1-Selection, 2-Happy, 3-Unhappy, 4-Alarm)
        self._model = StateModel(5, self, debug=True)

        # Register buttons, sensors, and timers with model
        self._model.addButton(self._btn_green)
        self._model.addButton(self._btn_red)
        self._model.addSensor(self._uss)
        self._model.addTimer(self._timer_timeout)

        # Custom event for manager alarm threshold trigger
        self._model.addCustomEvent("feedback_below_threshold")

        # 4. Define Transition Table
        # State 0: Welcome -> Selection on visitor approach (uss_trip) OR button press, or Alarm if stats low
        self._model.addTransition(0, ["uss_trip", "green_press", "red_press"], 1)
        self._model.addTransition(0, ["feedback_below_threshold"], 4)

        # State 1: Selection -> Happy on green press, Unhappy on red press, or Welcome on timeout
        self._model.addTransition(1, ["green_press"], 2)
        self._model.addTransition(1, ["red_press"], 3)
        self._model.addTransition(1, ["timer_timeout"], 0)

        # State 2: Happy -> Welcome after timeout
        self._model.addTransition(2, ["timer_timeout"], 0)

        # State 3: Unhappy -> Welcome after timeout, or Alarm if percentage drops below threshold
        self._model.addTransition(3, ["timer_timeout"], 0)
        self._model.addTransition(3, ["feedback_below_threshold"], 4)

        # State 4: Alarm -> Welcome on green button press (manager reset)
        self._model.addTransition(4, ["green_press"], 0)

    def stateEntered(self, state, event):
        """
        Performs **entry actions** for the given state.

        Parameters:
        ----------
        state : int
            The state number being entered (`0` to `4`)
        event : str
            The event that triggered the transition

        Examples:
        ---------
        1. Enter State 0 (Welcome):
           `controller.stateEntered(0, "no_event")`
        2. Enter State 1 (Selection):
           `controller.stateEntered(1, "uss_trip")`
        """
        Log.d(f"State {state} entered on event {event}")
        if state == 0:
            level = self._stats.get_light_level()
            if level > 0:
                self._lightstrip.setColor(GREEN, level)
            else:
                self._lightstrip.off()
            self._display.clear()
            self._display.showText("Welcome to Kiosk", 0, 0)
            pct = self._stats.calculate_percentage()
            self._display.showText(f"Rate: {pct:.0f}% OK    ", 1, 0)

        elif state == 1:
            self._lightstrip.setColor(BLUE, 8)
            self._display.clear()
            self._display.showText("Rate your visit:", 0, 0)
            self._display.showText("<3 Green  >2 Red", 1, 0)
            self._timer_timeout.start(5)

        elif state == 2:
            self._stats.add_happy()
            self._lightstrip.setColor(GREEN, self._stats.get_light_level() or 8)
            self._display.clear()
            self._display.showText("Thank you", 0, 0)
            self._display.showText("Positive feedback", 1, 0)
            try:
                for tone in (523, 659, 784):
                    self._buzzer.play(tone)
                    time.sleep(0.1)
                self._buzzer.stop()
            except Exception:
                pass
            self._timer_timeout.start(5)

        elif state == 3:
            self._stats.add_unhappy()
            self._lightstrip.setColor(RED, 8)
            self._display.clear()
            self._display.showText("Sorry to hear.", 0, 0)
            self._display.showText("Feedback noted", 1, 0)
            try:
                self._buzzer.play(200)
                time.sleep(0.3)
                self._buzzer.stop()
            except Exception:
                pass

            if self._stats.calculate_percentage() < self._threshold_pct and self._stats.get_total_count() >= 3:
                self._model.processEvent("feedback_below_threshold")
            else:
                self._timer_timeout.start(5)

        elif state == 4:
            self._lightstrip.setColor(RED, 8)
            self._display.clear()
            self._display.showText("Call Manager", 0, 0)
            pct = self._stats.calculate_percentage()
            self._display.showText(f"Rating {pct:.0f}% <30%", 1, 0)
            Log.w("ALERT: Satisfaction rating below 30%! Manager action required.")

    def stateLeft(self, state, event):
        """
        Performs **exit actions** when leaving the specified state.

        Parameters:
        ----------
        state : int
            The state number being exited (`0` to `4`)
        event : str
            The event that caused the exit

        Examples:
        ---------
        1. Exit State 1 (Selection):
           `controller.stateLeft(1, "green_press")`
        2. Exit State 4 (Alarm) and reset statistics:
           `controller.stateLeft(4, "green_press")`
        """
        Log.d(f"State {state} exited on event {event}")
        if state in [1, 2, 3]:
            self._timer_timeout.cancel()
        elif state == 4:
            self._stats.reset()
            self._buzzer.stop()

    def stateEvent(self, state, event) -> bool:
        """
        Handles **in-state events** that do not trigger a transition.

        Parameters:
        ----------
        state : int
            Current active state number (`0` to `4`)
        event : str
            The event string received

        Examples:
        ---------
        1. Check in-state event handling:
           `controller.stateEvent(0, "no_event")`
        2. Verify default return is False:
           `assert controller.stateEvent(0, "no_event") is False`
        """
        return False

    def stateDo(self, state):
        """
        Performs continuous **do activities** for the currently active state.

        Parameters:
        ----------
        state : int
            Current active state number (`0` to `4`)

        Examples:
        ---------
        1. Perform State 4 do action (plays 2-tone alarm):
           `controller.stateDo(4)`
        2. Perform State 0 do action:
           `controller.stateDo(0)`
        """
        if state == 4:
            try:
                self._buzzer.play(880)
                time.sleep(0.2)
                self._buzzer.play(440)
                time.sleep(0.2)
                self._buzzer.stop()
            except Exception:
                time.sleep(0.4)

    def run(self):
        """
        Starts and runs the **StateModel** event loop.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Start the kiosk state model:
           `controller.run()`
        2. Run inside a try/except block:
           `try: controller.run()`
           `except KeyboardInterrupt: controller.stop()`
        """
        Log.i("FeedbackController: Starting state model execution")
        self._model.run()

    def stop(self):
        """
        Stops the **StateModel** event loop and cleans up timers and handlers.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Stop the kiosk state model:
           `controller.stop()`
        2. Stop on interrupt:
           `controller.stop()`
        """
        Log.i("FeedbackController: Stopping state model")
        self._model.stop()


# Alias matching UML diagram capitalization
FeedBackController = FeedbackController


if __name__ == "__main__":
    controller = FeedbackController()
    try:
        controller.run()
    except KeyboardInterrupt:
        controller.stop()
