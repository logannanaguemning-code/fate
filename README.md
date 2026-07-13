# fate — Controller Remapper & Macro Engine

Remap any controller's buttons to keyboard input, and trigger multi-key macros from button combos. Works with Xbox, PlayStation, and generic USB/Bluetooth controllers — anything your OS already recognizes as a gamepad.

**[Project page →](https://logannanaguemning-code.github.io/fate/)**

## What it does

- Reads controller input via your OS's standard joystick/HID drivers (no drivers, no console modification)
- Maps individual buttons to keyboard keys
- Fires macros (sequences of key presses, holds, and delays) from button combos
- Config-driven: swap profiles per game without touching code

## What it doesn't do

This talks to your controller and your keyboard only, at the OS level. It doesn't modify, patch, or bypass authentication on any console or controller firmware — it just listens to input your OS already exposes and emits keystrokes in response.

## Install

```bash
git clone https://github.com/logannanaguemning-code/fate.git
cd fate
pip install -r requirements.txt
```

## Usage

Check your controller is detected:

```bash
python remapper/main.py --list
```

Run with the default profile:

```bash
python remapper/main.py
```

Run with a custom profile:

```bash
python remapper/main.py --profile remapper/profiles/my_profile.json
```

## Writing a profile

Profiles are JSON. `button_map` is a simple 1:1 button → key mapping. `macros` fires a sequence of key actions when a specific combo of buttons is pressed together (keys are button indices from `--list`, joined with `+`).

```json
{
  "controller_index": 0,
  "deadzone": 0.15,
  "button_map": {
    "0": "space",
    "1": "e"
  },
  "macros": {
    "4+5": [["ctrl", "down"], ["c", "tap"], ["ctrl", "up"]]
  }
}
```

## Roadmap

- [x] Button → keyboard remapping
- [x] Combo-triggered macros
- [x] Per-game profiles
- [ ] Analog stick → key/mouse mapping
- [ ] GUI profile editor
- [ ] Macro recorder (record real input instead of hand-writing JSON)

## Notes

Using macros or remapped input may violate the terms of service of some online games — check the rules for whatever you're playing before using this competitively.

## License

MIT
