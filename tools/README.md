# RDI Web Generator Tools

This directory contains utility scripts for generating code and assets used by the Rando-Dalton Imperial website.

## Scripts

### `prepatch_rom.py`

Applies the base patch to a ROM file (`ct.sfc`) and saves preprocessed outputs:
- `post_config.pkl` — prepatched configuration data
- `prepatched_rom.pkl` — patched ROM data

These files are used later by the randomizer to speed up seed generation. Run this once before generating presets or forms.

### `create_preset_buttons.py`

Generates HTML for preset buttons on the main index page and TOML generator form. It reads the list of available presets from `ctrando.arguments.Presets` and writes a file `preset_buttons.html`. This ensures the website always reflects the latest preset definitions without manual updates.

### `create_toml_gen_form.py`

This script reads the randomizer's argument specification data and generates the corresponding HTML form controls (toggles, sliders, choices, etc.) for each parameter. The output pages are used by the TOML generator form to let users create custom randomizer settings files.

## Usage

These scripts are automatically executed by the Docker container startup script when the container starts. This ensures that all generated outputs (`post_config.pkl`, `prepatched_rom.pkl`, and the HTML pages) remain synchronized with any changes to the randomizer code. They can be run manually, but it is not necessary.
