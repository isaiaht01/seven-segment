#!/usr/bin/python

# seven-segment module Main function
# Author: Eddy Ferre - ferree@seattleu.edu

from traceback import print_exc
from sys import stdout
from os import path
from re import compile
from argparse import ArgumentParser
from time import monotonic, sleep
from math import ceil

from .display import *
from .clock import Clock


def button_released():
    # Detect a full press and release
    if get_button_pressed():
        sleep(0.03)
        if get_button_pressed():
            while get_button_pressed():
                sleep(0.01)
            sleep(0.03)
            return True
    return False


def run_stopwatch():
    state = 0
    elapsed = 0.0
    start_time = 0.0

    set_led(False)

    while True:
        now = monotonic()

        if state == 1:
            elapsed = now - start_time

        # Display seconds with one decimal place
        tenths = min(int(elapsed * 10), 9999)
        digits = f"{tenths:04d}"

        # Decimal point after third digit
        activate_displays(
            digits,
            decimal_point=[False, False, True, False]
        )

        if state == 0:
            set_led(False)
        elif state == 1:
            set_led(int(now * 2) % 2 == 0)
        else:
            set_led(True)

        if button_released():
            if state == 0:
                elapsed = 0.0
                start_time = monotonic()
                state = 1
            elif state == 1:
                elapsed = monotonic() - start_time
                state = 2
            else:
                elapsed = 0.0
                state = 0


def run_timer(timerstart):
    if timerstart is None:
        raise ValueError("Use -t MM:SS")

    parts = timerstart.split(":")
    if len(parts) != 2:
        raise ValueError("Timer format must be MM:SS")

    minutes, seconds = map(int, parts)

    if not (0 <= minutes <= 99 and 0 <= seconds <= 59):
        raise ValueError("Invalid timer duration")

    total = minutes * 60 + seconds
    end_time = monotonic() + total

    set_led(False)

    while True:
        now = monotonic()
        remaining = max(0, ceil(end_time - now))

        mins = remaining // 60
        secs = remaining % 60
        digits = f"{mins:02d}{secs:02d}"

        activate_displays(
            digits,
            set_colon=(int(now * 2) % 2 == 0)
        )

        if remaining == 0:
            break

    # Timer finished: blink LED until button
    while True:
        now = monotonic()
        activate_displays("0000", set_colon=True)
        set_led(int(now * 2) % 2 == 0)

        if button_released():
            set_led(False)
            break


def main():
    clock = None
    channels_set = False
    clock_pattern = compile(r"([12]?)(\d):([0-5])(\d)")

    try:
        parser = ArgumentParser(description='Seven-Segment Clock Display')
        parser.add_argument('mode',
                            default='clock',
                            const='clock',
                            nargs='?',
                            choices=['clock', 'timer', 'stopwatch', 'freeform'],
                            help='list of modes (default: %(default)s)')
        parser.add_argument('-a',
                            '--alarm',
                            action='store',
                            help="Alarm time, H:MM format (24hr)")
        parser.add_argument('-m',
                            '--music',
                            action='store',
                            help="Music to play as alarm")
        parser.add_argument('-t',
                            '--timerstart',
                            action='store',
                            help="Timer start, MM:SS format")

        args = parser.parse_args()

        # Setup and Initialize the GPIO pins
        init_display(channels_set)

        if args.mode == 'clock':
            alarm = None
            music_file = None
            if args.alarm is not None:
                m = clock_pattern.match(args.alarm)
                if m is None:
                    print(f"ERROR: Invalid alarm argument '{args.alarm}'. Must be 'H:MM'")
                else:
                    print(f"Alarm set to {args.alarm}")
                    alarm = args.alarm.replace(":", "")
                    if m.group(1) == '':
                        alarm = " " + alarm
                    if args.music is not None:
                        if path.isfile(args.music):
                            music_file = args.music
                        else:
                            print(f"ERROR: Cannot find '{args.music}' file")

            print("Running 'clock' mode ...")
            clock = Clock()
            clock.set_alarm(alarm)
            clock.set_music(music_file)
            clock.start()
            # Stay in 'clock' mode until Ctrl+c
            while True:
                sleep(1.0)

        elif args.mode == 'stopwatch':
            run_stopwatch()

        elif args.mode == 'timer':
            run_timer(args.timerstart)

        else:   # args.mode == 'freeform'

            # Let user enter 4 characters
            string = input("Enter what you want the clock display to print: ")

            # Parse Clock entry
            m = clock_pattern.match(string)
            if m is None:
                pass
            elif m.group(1) == '2' and m.group(2) not in "0123":
                raise ValueError("Clock - Invalid entry")
            else:
                print("Valid clock entry")
                # Sets the Digits
                if m.group(1) == '':
                    digits = " "
                else:
                    digits = m.group(1)
                for i in range(2, 5):
                    digits += m.group(i)
                while True:
                    activate_displays(digits, set_colon=True)
            print("not a clock entry")

            # Parse number
            try:
                # noinspection PyUnusedLocal
                value = float(string)
                print("Valid number")
                # TODO: write your code here!
                # Watch for negative values, floating points...
            except ValueError:
                pass
                print("not a number")

            # Parse anything else
            valid_char = ''.join(re.escape(c) for c in SEGS_FOR_CHAR.keys())
            print(valid_char)
            pattern = compile(
                rf"([{valid_char}])?(\.)?([{valid_char}])?(\.)?(:)?([{valid_char}])?(\.)?(')?([{valid_char}])?(\.)?")
            m = pattern.match(string)
            if m is None:
                pass
            elif m.groups() != (None, None, None, None, None, None, None, None, None, None):
                digit_group_indexes = [1, 3, 6, 9]
                dp_group_indexes = [2, 4, 7, 10]
                print(m.groups())
                digits = ""
                dp = [False] * 4
                for i in digit_group_indexes:
                    if m.group(i) is None:
                        digits += " "
                    else:
                        digits += m.group(i)
                dp_idx = 0
                for i in dp_group_indexes:
                    dp[dp_idx] = m.group(i) is not None
                    dp_idx += 1
                set_colon = m.group(5) is not None
                set_thousand = m.group(8) is not None
                while True:
                    activate_displays(digits, decimal_point=dp, set_colon=set_colon, set_thousand=set_thousand)

            digits = "-Err"
            print(f"Could not parse entry, showing: '{digits}'")
            while True:
                activate_displays(digits)

    except KeyboardInterrupt:
        if clock is not None:
            clock.stop()
        print("\b\b  \nCtrl+c pressed, exiting")
    except ValueError as e:
        print(e)
    except Exception:
        print("-" * 60)
        print_exc(file=stdout)
        print("-" * 60)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
