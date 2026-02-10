# QuietConsole

QuietConsole is an NVDA add-on for noisy terminal workflows. It suppresses high-frequency console speech events, and provides a live plain-text view for easier reading with speech and braille.

## Key Features

- Global quiet mode to reduce event/speech spam in consoles
- Works in `cmd.exe`, `conhost.exe`, `powershell.exe`, `pwsh.exe`, and Windows Terminal hosts (`windowsterminal.exe`, `wt.exe`, `openconsole.exe`)
- Optional extreme suppression mode for aggressive speech cancellation
- Live plain-text view window for terminal output:
  - `NVDA+Shift+V` or `NVDA+Alt+V` opens/closes the view
  - `End` jumps to the latest line start
  - `F5` toggles follow-bottom vs fixed-line behavior
  - `Esc` closes the view
- Optional suppression logging for troubleshooting

## Settings

QuietConsole adds a settings panel in NVDA:
- `NVDA -> Preferences -> Settings -> Quiet Console`
- Gestures for quiet mode and live plain-text view can be changed in Input Gestures.

## Install

Download the [latest release](https://github.com/sylvanova/QuietConsole/releases/latest) from this repository, then install the `.nvda-addon` file in NVDA via:
- `Tools -> Manage add-ons -> Install`

## Credits

This add-on was developed with significant AI assistance.
