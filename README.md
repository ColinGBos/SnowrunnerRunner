# SnowrunnerRunner

A tool for processing and managing SnowRunner game data.

## Description
SnowrunnerRunner is a Python-based utility designed to parse, analyze, modify, and summarize game data files (XML) for the game SnowRunner.

## Features
- A number of tweaks are applied universally (improved traction values, normalized steering angles, improved fuel and suspension values).
- Contains a patching system for applying custom modifications to game data based on string replacement.
- Outputs json files with game data, xlsx table summaries of game data, an optional comparison of current pak files with the pts server, and modified files in the output folder in the format to copy into the pak using WinRar.

## Usage
1. Extract pak intial contents to initial/[media]/.., and initial/[strings]/..
2. Add any adjustments to the adjustments.json file
3. Optionally, include extracted mod files in the input/mods folder to include in the summary output. Should be mods/mod_name/classes/..
4. Run `src/main.py` for the data tweaks and summary output or `src/data-process.py` for just the summary process.
5. Overwrite the modified files in the output folder into the initial pak in either steam or epic install location using WinRar.

## License
MIT
