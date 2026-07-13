"""
Controller Remapper & Macro Engine
-----------------------------------
Reads input from any controller connected to your PC (Xbox, PS4, PS5,
generic USB/Bluetooth gamepads — anything your OS already recognizes as
a joystick) and lets you remap buttons/axes to keyboard keys, and fire
macros (sequences of key presses) from button combos.

This works entirely at the OS/driver level via pygame's joystick API —
it does NOT talk to any console, and does not touch controller
authentication/security. It's for remapping input on your PC only.

Usage:
    python main.py                     # uses profiles/default.json
    python main.py --profile my.json   # use a custom profile
    python main.py --list              # list connected controllers
"""

import argparse
import json
import sys
import time
from pathlib import Path

import pygame

try:
    import keyboard  # pip install keyboard
except ImportError:
    keyboard = None


PROFILES_DIR = Path(__file__).parent / "profiles"


def list_controllers():
    pygame.init()
    pygame.joystick.init()
    count = pygame.joystick.get_count()
    if count == 0:
        print("No controllers detected.")
        return
    for i in range(count):
        js = pygame.joystick.Joystick(i)
        js.init()
        print(f"[{i}] {js.get_name()}  "
              f"(buttons={js.get_numbuttons()}, axes={js.get_numaxes()})")


def load_profile(path: Path) -> dict:
    with open(path, "r") as f:
        return json.load(f)


class RemapEngine:
    """
    Profile format (see profiles/default.json):
    {
      "controller_index": 0,
      "deadzone": 0.15,
      "button_map": { "0": "space", "1": "e" },
      "macros": {
        "4+5": [["ctrl", "down"], ["c", "tap"], ["ctrl", "up"]]
      }
    }
    """

    def __init__(self, profile: dict):
        if keyboard is None:
            sys.exit("Missing dependency: pip install keyboard")

        pygame.init()
        pygame.joystick.init()

        idx = profile.get("controller_index", 0)
        if pygame.joystick.get_count() <= idx:
            sys.exit(f"No controller at index {idx}. Run --list to check.")

        self.joystick = pygame.joystick.Joystick(idx)
        self.joystick.init()
        self.deadzone = profile.get("deadzone", 0.15)
        self.button_map = {int(k): v for k, v in profile.get("button_map", {}).items()}
        self.macros = profile.get("macros", {})

        self.pressed_buttons = set()
        self.held_keys = set()

        print(f"Connected: {self.joystick.get_name()}")
        print(f"Remapping {len(self.button_map)} buttons, "
              f"{len(self.macros)} macros. Ctrl+C to quit.")

    def run(self):
        clock = pygame.time.Clock()
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        self._on_button(event.button, True)
                    elif event.type == pygame.JOYBUTTONUP:
                        self._on_button(event.button, False)
                clock.tick(120)
        except KeyboardInterrupt:
            self._release_all()
            print("\nStopped.")

    def _on_button(self, button: int, is_down: bool):
        if is_down:
            self.pressed_buttons.add(button)
        else:
            self.pressed_buttons.discard(button)

        # Check macros first (combo match)
        combo_key = "+".join(str(b) for b in sorted(self.pressed_buttons))
        if is_down and combo_key in self.macros:
            self._fire_macro(self.macros[combo_key])
            return

        # Simple 1:1 remap
        key = self.button_map.get(button)
        if key:
            if is_down:
                keyboard.press(key)
                self.held_keys.add(key)
            else:
                keyboard.release(key)
                self.held_keys.discard(key)

    def _fire_macro(self, steps):
        for step in steps:
            key, action = step[0], step[1]
            if action == "down":
                keyboard.press(key)
            elif action == "up":
                keyboard.release(key)
            elif action == "tap":
                keyboard.press(key)
                time.sleep(0.02)
                keyboard.release(key)
            if len(step) > 2:
                time.sleep(step[2])

    def _release_all(self):
        for key in list(self.held_keys):
            keyboard.release(key)


def main():
    parser = argparse.ArgumentParser(description="Controller remapper & macro engine")
    parser.add_argument("--profile", default=str(PROFILES_DIR / "default.json"))
    parser.add_argument("--list", action="store_true", help="List connected controllers and exit")
    args = parser.parse_args()

    if args.list:
        list_controllers()
        return

    profile = load_profile(Path(args.profile))
    engine = RemapEngine(profile)
    engine.run()


if __name__ == "__main__":
    main()
