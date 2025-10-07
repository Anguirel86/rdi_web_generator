"""
This script autogenerates the html for the preset buttons on the
main randomizer index page.  This allows the index page to always
be up to date with the latest preset file changes.
"""

import importlib.resources
import io
from pathlib import Path


def main():
    # Get all settings files from the presets directory in
    # the ctrando package
    preset_files = importlib.resources.contents('ctrando.presets')

    html_buffer = io.StringIO()

    for file in preset_files:
        name = Path(file).stem
        html_buffer.write(
            f'<button class="btn btn-primary mt-1 mb-1" type="button" onclick="set_preset(\'{name}\')">{name}</button>\n')

    html_buffer.seek(0)
    with open('preset_buttons.html', 'w') as file:
        file.write(html_buffer.read())


if __name__ == "__main__":
    main()
