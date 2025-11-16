# QuietConsole NVDA add-on

QuietConsole keeps NVDA responsive in classic consoles (`cmd.exe` / `conhost.exe`) by letting you toggle a "quiet mode" that suppresses noisy text updates. It also adds a quick command to read the last lines without re-enabling live updates.

## Gestures (rebind in NVDA → Preferences → Input Gestures, search "Quiet Console")
* `NVDA+Shift+C` — Toggle quiet mode (global for all consoles). On: suppress caret/value/text/name-change events; Off: behave like stock NVDA. When turning on, queued speech is cancelled.
* `NVDA+Shift+R` — Read the last 30 lines from the console and move the review cursor to the bottom (configurable in `appModules/cmd.py`).

## Install
1. In NVDA: Tools → Manage add-ons → Install, select `QuietConsole-0.1.0.nvda-addon`, restart NVDA.
2. Focus a console window and use the gestures above. The current quiet-mode state is saved across restarts.

## Configuration knobs (edit `appModules/cmd.py`)
* `DEFAULT_QUIET_MODE` — `False` by default; set `True` if you want consoles to start quiet.
* `READ_LAST_LINES` — number of lines `NVDA+Shift+R` reads.
* `LOG_SUPPRESSION` — set `True` to log every suppressed event when quiet mode is on.

## Notes
* Quiet mode is global: toggling in one console applies to all.
* When quiet mode is on, we fully drop the noisy events so NVDA won’t try to speak them; when off, events flow unchanged.
