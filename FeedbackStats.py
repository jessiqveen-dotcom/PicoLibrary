"""
# FeedbackStats.py
# Tracks happy and unhappy user feedback counts and computes summary statistics
# Author: jessiqveen-dotcom
"""

from Log import *


class FeedbackStats:
    """
    Tracks store customer **happy** and **unhappy** feedback counts and calculates
    aggregate metrics such as total responses, happy percentage, and NeoPixel light strip levels.

    Parameters:
    ----------
    happy_count : int, optional
        Initial count of happy feedback responses (default: 0)
    unhappy_count : int, optional
        Initial count of unhappy feedback responses (default: 0)
    max_leds : int, optional
        Default number of LEDs on the LightStrip for light level calculations (default: 8)

    Examples:
    ---------
    1. Create a FeedbackStats tracker and record responses:
       `stats = FeedbackStats()`
       `stats.add_happy()`
       `stats.add_unhappy()`
    2. Retrieve statistics and reset:
       `total = stats.get_total_count()`
       `pct = stats.calculate_percentage()`
       `leds = stats.get_light_level()`
       `stats.reset()`
    """

    def __init__(self, happy_count: int = 0, unhappy_count: int = 0, max_leds: int = 8):
        self._happy_count = int(happy_count)
        self._unhappy_count = int(unhappy_count)
        self._max_leds = int(max_leds)
        self._happy_streak = 0
        Log.i(
            f"FeedbackStats initialized (happy={self._happy_count}, "
            f"unhappy={self._unhappy_count}, max_leds={self._max_leds})"
        )

    @property
    def happy_streak(self) -> int:
        """Returns the current consecutive happy feedback streak."""
        return self._happy_streak

    @property
    def happy_count(self) -> int:
        """Returns the current happy feedback count."""
        return self._happy_count

    @happy_count.setter
    def happy_count(self, value: int) -> None:
        self._happy_count = int(value)

    @property
    def unhappy_count(self) -> int:
        """Returns the current unhappy feedback count."""
        return self._unhappy_count

    @unhappy_count.setter
    def unhappy_count(self, value: int) -> None:
        self._unhappy_count = int(value)

    def add_happy(self) -> int:
        """
        Increments the **happy** feedback counter by 1.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Record a happy customer response:
           `stats.add_happy()`
        2. Record and capture the updated happy count:
           `count = stats.add_happy()`
        """
        self._happy_count += 1
        self._happy_streak += 1
        Log.i(
            f"Added happy feedback (happy_count={self._happy_count}, "
            f"streak={self._happy_streak})"
        )
        return self._happy_count

    def add_unhappy(self) -> int:
        """
        Increments the **unhappy** feedback counter by 1.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Record an unhappy customer response:
           `stats.add_unhappy()`
        2. Record and capture the updated unhappy count:
           `count = stats.add_unhappy()`
        """
        self._unhappy_count += 1
        self._happy_streak = 0
        Log.i(f"Added unhappy feedback (unhappy_count={self._unhappy_count})")
        return self._unhappy_count

    def get_total_count(self) -> int:
        """
        Calculates and returns the **total** number of feedback responses (`happy_count + unhappy_count`).

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Get total responses collected:
           `total = stats.get_total_count()`
        2. Check if any feedback has been recorded:
           `if stats.get_total_count() > 0: ...`
        """
        total = self._happy_count + self._unhappy_count
        Log.i(f"Total feedback count: {total}")
        return total

    def calculate_percentage(self) -> float:
        """
        Calculates the **percentage of happy feedback** out of the total responses (`0.0` to `100.0`).
        Returns `0.0` when no feedback has been recorded yet.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Calculate the current satisfaction percentage:
           `pct = stats.calculate_percentage()`
        2. Format percentage for an LCD display:
           `text = f"Happy: {stats.calculate_percentage():.0f}%"`
        """
        total = self._happy_count + self._unhappy_count
        if total == 0:
            Log.i("Total count is 0; happy percentage is 0.0%")
            return 0.0
        percentage = (self._happy_count / total) * 100.0
        Log.i(f"Calculated happy percentage: {percentage:.1f}%")
        return percentage

    def get_light_level(self, max_leds: int = None) -> int:
        """
        Maps the current **happy feedback percentage** to a number of LEDs to illuminate on a
        *LightStrip* (`0` up to `max_leds`).

        Parameters:
        ----------
        max_leds : int, optional
            Total number of LEDs available on the light strip (default: `self._max_leds`, which defaults to 8)

        Examples:
        ---------
        1. Get the number of pixels to light on the default 8-LED strip:
           `num_pixels = stats.get_light_level()`
        2. Get the number of pixels to light on a 16-LED strip:
           `num_pixels = stats.get_light_level(max_leds=16)`
        """
        leds = self._max_leds if max_leds is None else int(max_leds)
        total = self._happy_count + self._unhappy_count
        if total == 0 or leds <= 0:
            Log.i("Light level calculated: 0 LEDs")
            return 0
        percentage = (self._happy_count / total) * 100.0
        level = int(round((percentage / 100.0) * leds))
        Log.i(f"Light level calculated: {level}/{leds} LEDs ({percentage:.1f}%)")
        return level

    def get_summary(self) -> str:
        """
        Returns a compact 16-character summary string for row 1 of the LCD display
        showing happy count, unhappy count, and satisfaction percentage.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Format summary for LCD line 1:
           `summary = stats.get_summary()`
        2. Display on LCD:
           `display.showText(stats.get_summary(), 1, 0)`
        """
        total = self._happy_count + self._unhappy_count
        if total == 0:
            return "Ready for visit!"
        pct = int(round((self._happy_count / total) * 100.0))
        return f"H:{self._happy_count} U:{self._unhappy_count} ({pct}%)"

    def reset(self) -> None:
        """
        Resets both **happy_count** and **unhappy_count** back to `0`.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. Reset all feedback counts at the end of the day:
           `stats.reset()`
        2. Reset and verify count is zero:
           `stats.reset(); assert stats.get_total_count() == 0`
        """
        self._happy_count = 0
        self._unhappy_count = 0
        self._happy_streak = 0
        Log.i("FeedbackStats counts reset to 0")


if __name__ == "__main__":
    Log.i("Starting self-contained verification for FeedbackStats")

    stats = FeedbackStats()
    assert stats.happy_count == 0
    assert stats.unhappy_count == 0
    assert stats.get_total_count() == 0
    assert stats.calculate_percentage() == 0.0
    assert stats.get_light_level() == 0

    # Add 3 happy and 1 unhappy (75% happy -> 6 of 8 LEDs)
    stats.add_happy()
    stats.add_happy()
    stats.add_happy()
    stats.add_unhappy()

    assert stats.happy_count == 3
    assert stats.unhappy_count == 1
    assert stats.get_total_count() == 4
    assert stats.calculate_percentage() == 75.0
    assert stats.get_light_level() == 6
    assert stats.get_light_level(max_leds=16) == 12

    # Reset and verify
    stats.reset()
    assert stats.happy_count == 0
    assert stats.unhappy_count == 0
    assert stats.get_total_count() == 0
    assert stats.calculate_percentage() == 0.0
    assert stats.get_light_level() == 0

    Log.i("Testing complete - all FeedbackStats checks passed")
