"""
This script autogenerates the html for the preset buttons on the
main randomizer index page.  This allows the index page to always
be up to date with the latest preset file changes.
"""

import io

from ctrando.arguments import arguments


def main():

    html_buffer = io.StringIO()

    # Get the list of presets from the rando
    for preset in arguments.Presets:
        display_name = preset.value.name
        html_buffer.write(
            f'<button class="btn btn-primary mt-1 mb-1 preset-button" type="button" onclick="setPreset(this, \'{preset.name}\')">{display_name}</button>\n')

    html_buffer.seek(0)
    with open('preset_buttons.html', 'w') as file:
        file.write(html_buffer.read())


if __name__ == "__main__":
    main()
