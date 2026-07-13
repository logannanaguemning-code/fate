"""
Controller Remapper & Macro Engin
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
    Profile format (see profiles/default.json and profiles/advanced.json):
    {
      "controller_index": 0,
      "deadzone": 0.15,

      "button_map": {
        "0": "space",                                 // shorthand = hold mode
        "1": { "key": "e", "mode": "tap" },
        "2": { "key": "capslock", "mode": "toggle" }
      },

      "layers": {
        "trigger_button": 6,                           // hold this button...
        "map": { "0": "1", "1": "2" }                  // ...to use this map instead
      },

      "macros": {
        "4+5": {
          "steps": [["ctrl", "down"], ["c", "tap"], ["ctrl", "up"]],
          "cooldown_ms": 300,                           // min gap between fires
          "repeat": 1                                   // times to run the sequence
        }
      }
    }

    button_map / layer map entries accept either a plain key string ("hold"
    mode, matches old profiles) or an object with "key" + "mode", where mode
    is one of: "hold" (default), "tap", "toggle".

    macros entries accept either the old bare list-of-steps format, or the
    object format above with cooldown_ms / repeat.
    """

    VALID_MODES = {"hold", "tap", "toggle"}

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

        self.button_map = self._normalize_map(profile.get("button_map", {}))

        layers = profile.get("layers") or {}
        self.layer_trigger = layers.get("trigger_button")
        self.layer_map = self._normalize_map(layers.get("map", {}))
        self.layer_active = False

        self.macros = self._normalize_macros(profile.get("macros", {}))
        self._macro_last_fired = {}  # combo_key -> monotonic time

        self.pressed_buttons = set()
        self.held_keys = set()
        self.toggle_state = {}  # button -> bool (currently "on")

        print(f"Connected: {self.joystick.get_name()}")
        print(f"Remapping {len(self.button_map)} buttons, "
              f"{len(self.macros)} macros"
              + (f", 1 layer (trigger={self.layer_trigger})" if self.layer_trigger is not None else "")
              + ". Ctrl+C to quit.")

    # ---------- profile normalization ----------

    def _normalize_map(self, raw_map: dict) -> dict:
        """Turn every entry into {"key": str, "mode": str}."""
        normalized = {}
        for k, v in raw_map.items():
            if isinstance(v, str):
                normalized[int(k)] = {"key": v, "mode": "hold"}
            else:
                mode = v.get("mode", "hold")
                if mode not in self.VALID_MODES:
                    sys.exit(f"Invalid mode '{mode}' for button {k}. "
                             f"Use one of {sorted(self.VALID_MODES)}.")
                normalized[int(k)] = {"key": v["key"], "mode": mode}
        return normalized

    def _normalize_macros(self, raw_macros: dict) -> dict:
        normalized = {}
        for combo, v in raw_macros.items():
            if isinstance(v, list):
                normalized[combo] = {"steps": v, "cooldown_ms": 0, "repeat": 1}
            else:
                normalized[combo] = {
                    "steps": v["steps"],
                    "cooldown_ms": v.get("cooldown_ms", 0),
                    "repeat": v.get("repeat", 1),
                }
        return normalized

    # ---------- main loop ----------

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
        # Track the modifier layer before anything else, so the trigger
        # button itself never falls through to remapping/macros.
        if self.layer_trigger is not None and button == self.layer_trigger:
            self.layer_active = is_down
            return

        if is_down:
            self.pressed_buttons.add(button)
        else:
            self.pressed_buttons.discard(button)

        # Macros take priority over plain remapping (combo match, base layer only).
        combo_key = "+".join(str(b) for b in sorted(self.pressed_buttons))
        if is_down and combo_key in self.macros:
            self._fire_macro(combo_key)
            return

        active_map = self.layer_map if (self.layer_active and self.layer_map) else self.button_map
        binding = active_map.get(button)
        if not binding:
            return

        key, mode = binding["key"], binding["mode"]

        if mode == "hold":
            if is_down:
                keyboard.press(key)
                self.held_keys.add(key)
            else:
                keyboard.release(key)
                self.held_keys.discard(key)

        elif mode == "tap":
            if is_down:
                keyboard.press(key)
                time.sleep(0.02)
                keyboard.release(key)

        elif mode == "toggle":
            if is_down:
                on = not self.toggle_state.get(button, False)
                self.toggle_state[button] = on
                if on:
                    keyboard.press(key)
                    self.held_keys.add(key)
                else:
                    keyboard.release(key)
                    self.held_keys.discard(key)

    # ---------- macros ----------

    def _fire_macro(self, combo_key: str):
        macro = self.macros[combo_key]
        cooldown = macro["cooldown_ms"] / 1000.0
        now = time.monotonic()
        last = self._macro_last_fired.get(combo_key, 0)
        if now - last < cooldown:
            return  # still cooling down, ignore this trigger
        self._macro_last_fired[combo_key] = now

        for _ in range(max(1, macro["repeat"])):
            for step in macro["steps"]:
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
