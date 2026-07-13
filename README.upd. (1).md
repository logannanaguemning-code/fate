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

Profiles are JSON. Start simple:

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

See `remapper/profiles/advanced.json` for a full example of everything below.

### Button modes

By default a mapped button behaves like the original — held down while the button is held. You can change that per button:

```json
"button_map": {
  "0": "space",
  "1": { "key": "e", "mode": "tap" },
  "2": { "key": "capslock", "mode": "toggle" }
}
```

| mode | behavior |
|---|---|
| `hold` (default) | key is down exactly while the button is down |
| `tap` | one quick press/release each time the button goes down |
| `toggle` | first press turns the key "on" and holds it; next press releases it |

### Modifier layers

Hold one button to temporarily swap in a different button map — like a shift key for your controller:

```json
"layers": {
  "trigger_button": 6,
  "map": {
    "0": "1",
    "1": "2"
  }
}
```

While button `6` is held, buttons `0` and `1` use the layer's map instead of the base `button_map`. Release it and you're back to normal. The trigger button itself never fires its own action.

### Macro cooldown & repeat

Macros can take an object instead of a bare list of steps, adding a minimum gap between triggers and/or repeating the sequence:

```json
"macros": {
  "4+5": {
    "steps": [["ctrl", "down"], ["c", "tap"], ["ctrl", "up"]],
    "cooldown_ms": 300,
    "repeat": 1
  }
}
```

`cooldown_ms` ignores re-triggers within that window (handy for combos you might accidentally hit twice). `repeat` runs the whole step sequence that many times in a row.

## Roadmap

- [x] Button → keyboard remapping
- [x] Combo-triggered macros
- [x] Per-game profiles
- [x] Toggle / tap button modes
- [x] Modifier layers
- [x] Macro cooldown & repeat
- [ ] Analog stick → key/mouse mapping
- [ ] GUI profile editor
- [ ] Macro recorder (record real input instead of hand-writing JSON)

## Notes

Using macros or remapped input may violate the terms of service of some online games — check the rules for whatever you're playing before using this competitively.
