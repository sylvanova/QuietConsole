# Repository Guidelines

## Project Structure & Module Organization
- `manifest.ini`, `README.md`, and localization assets describe the add-on for NVDA.
- `appModules/` holds platform-specific modules (`cmd`, `powershell`, `wt`, etc.) that share the QuietConsole logic; most changes land in `appModules/cmd.py`.
- `globalPlugins/quietConsole.py` exposes the NVDA settings panel; `doc/` and `locale/` mirror NVDA’s documentation requirements.
- Build output (`*.nvda-addon`) is kept at the repository root but ignored by the project so it can be rebuilt as needed.

## Build, Test, and Development Commands
- `python3 build-addon.py` *(example only)*: there isn’t a formal build script, but packaging is done by zipping the tracked files (see `QuietConsole-*.nvda-addon` generation in the root). Replicate this by running a Python script that bundles `manifest.ini`, directories under `appModules/`, `globalPlugins/`, `doc/`, and `locale/`.
- NVDA addons themselves don’t have unit tests here; manual testing occurs by installing the generated `.nvda-addon` in NVDA, toggling quiet mode, and exercising consoles.

## Coding Style & Naming Conventions
- Use four-space indentation for Python, matching NVDA’s existing style.
- Keep translation dictionaries and `_()` wrappers consistent: reuse existing keys when adding new strings (`appModules/cmd.py` and `globalPlugins/quietConsole.py` follow the pattern).
- All files stay ASCII-friendly, which aligns with NVDA’s recommendation.
- No automated linting tools are tracked, so rely on NVDA’s Python 3.10 compatibility standards when editing.

## Testing Guidelines
- There are no automated tests in this repository. Validate manually by reinstalling the built `.nvda-addon`, enabling quiet mode, and confirming speech suppression/read commands behave across `cmd.exe`, `powershell.exe`, `pwsh.exe`, and Windows Terminal.
- When adding behavior to `appModules/cmd.py`, riff the same logic into the other module wrappers so testing covers every console implementation via the shared inheritance.

## Commit & Pull Request Guidelines
- Keep commit messages descriptive and concise (as seen in history: e.g., “a lot more fiexed to the addon…”). Use present-tense verbs and mention the target area (module name or feature).
- Pull requests should describe user-facing changes, reference any relevant NVDA or GitHub issue IDs, and note how the addon was tested (console scenario, NVDA version).
- Include the regenerated `.nvda-addon` file matching the `manifest.ini` version whenever the code changes; mention within the PR description which build artifact was updated so reviewers can reinstall it.

## Agent Instructions
- Do not change Git author configuration (`user.name`/`user.email`) in this repo.
- Avoid rewriting translated strings unless absolutely necessary; update all locales whenever text changes to keep the `.ini` manifest translation metadata consistent.
- NVDA logs: current sessions write to `%LOCALAPPDATA%\Temp\nvda.log` (and sometimes `nvda-old.log`). If you need to inspect suppression behavior, tail that file (e.g., `tail -n 80 %LOCALAPPDATA%\\Temp\\nvda.log`). If “Log suppressed events” is off, toggle it in QuietConsole settings first, reproduce once, then read the log.
- Extreme mode: suppression logs include `extreme=<True/False>` when events are dropped. If you don’t see `QuietConsole suppressed …` lines after toggling extreme mode, reinstall the current package and re-save the setting so it applies to all consoles.
