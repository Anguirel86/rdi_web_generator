#!/bin/bash

# Autogenerate the toml generator html and python form code
python tools/create_toml_gen_form.py

if [[ $? -ne 0 ]]; then
    echo "Failed to generate toml_gen form"
    exit 1
fi

# Copy over the auto-generated html files
echo "Auto-generating TOML generator form..."
AUTOGEN_HTML_PATH=generator/templates/generator/toml_gen
mkdir -p $AUTOGEN_HTML_PATH
cp form_gen_output/html/* $AUTOGEN_HTML_PATH

# Copy over the auto-generated python form file
cp form_gen_output/toml_gen_form.py generator/
rm -r form_gen_output

# Autogenerate the preset buttons based on available preset files
echo "Creating preset button template..."
python tools/create_preset_buttons.py
cp preset_buttons.html $AUTOGEN_HTML_PATH
rm preset_buttons.html

# Generate the ROM files pre-patched with the base patch.
# This can be used to speed up subsequent randomizer calls
echo "Creating prepatched config and ctrom objects..."
python tools/prepatch_rom.py

# Handle db migrations and static files on container startup
python manage.py migrate
python manage.py collectstatic --no-input --clear

exec "$@"
