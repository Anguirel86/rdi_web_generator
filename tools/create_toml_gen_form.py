"""
This script autogenerates all of the toml form html based on the arg specs
returned by the randomizer arguments package.  The form contains a tab for
each of the major groupings of rando arguments.
"""

import io
import os

from ctrando.arguments import (
    arguments,
    argumenttypes
)


def create_toggle_control(flag_name: str, spec: argumenttypes.FlagArg, form_buffer: io.StringIO, reset_function_buffer: io.StringIO):
    """
    Generate HTML for a toggle for the given flag.
    """
    default_string = 'checked' if spec.default_value else ''
    toggle_control = f'''
        <div class="form-group form-check pl-0" data-toggle="tooltip" title="{spec.help_text}">
          <input type="checkbox" name="{{{{form.{flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}" data-toggle="toggle" {default_string}>
          <label for="{{{{form.{flag_name}.id_for_label}}}}">{flag_name}</label>
        </div>
    '''
    form_buffer.write(toggle_control)

    default_val = 'true' if spec.default_value else 'false'
    reset_function_buffer.write(
        f'$("#{{{{form.{flag_name}.id_for_label}}}}").prop("checked", {default_val}).change();\n')


def create_slider_control(flag_name: str, spec: argumenttypes.DiscreteNumericalArg, form_buffer: io.StringIO, reset_function_buffer: io.StringIO):
    """
    Generate HTML for a slider with the give min/max/interval
    """

    # The slider and text box should update each other on change
    slider_control = f'''
        <div class="form-group" data-toggle="tooltip" title="{spec.help_text}">
          <label for="{{{{form.{flag_name}.id_for_label}}}}" class="form-label mr-2">{flag_name}</label>
          <input type="range" class="form-range" name="{{{{form.{flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}" min="{spec.min_value}" max="{spec.max_value}" step="{spec.interval}" value="{spec.default_value}">
          <input type="text" id="{{{{form.{flag_name}.id_for_label}}}}_text" form="none" size="1" value="{spec.default_value}">
        </div>

        <script>
          const slider_{flag_name} = document.getElementById("{{{{form.{flag_name}.id_for_label}}}}");
          const text_{flag_name} = document.getElementById("{{{{form.{flag_name}.id_for_label}}}}_text");

          slider_{flag_name}.addEventListener("input", function(event) {{
            text_{flag_name}.value = slider_{flag_name}.value.toString();
          }});

          text_{flag_name}.addEventListener("input", function(event) {{
            slider_{flag_name}.value = text_{flag_name}.value;
          }});
        </script>
        '''

    form_buffer.write(slider_control)

    reset_function_buffer.write(
        f'$("#{{{{form.{flag_name}.id_for_label}}}}").val({spec.default_value}).change();\n')

    reset_function_buffer.write(
        f'$("#{{{{form.{flag_name}.id_for_label}}}}_text").val({spec.default_value}).change();\n')


def create_choice_control(flag_name: str, spec: argumenttypes.DiscreteCategorialArg, form_buffer: io.StringIO, reset_function_buffer: io.StringIO):
    """
    Generate HTML for a dropdown box for the provided choice list
    """
    form_buffer.write(
        f'<div class="form-group" data-toggle="tooltip" title="{spec.help_text}">\n')
    form_buffer.write(f'  <label for="{{{{form.{flag_name}.id_for_label}}}}">{
                      flag_name}:</label>\n')
    form_buffer.write(f'  <select class="form-control" name="{{{{form.{
                      flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}">\n')
    for choice in spec.choices:
        selected_string = 'selected' if choice == spec.default_value else ''
        form_buffer.write(f'    <option value="{choice}" {
                          selected_string}>{choice}</option>\n')
    form_buffer.write('  </select>\n')
    form_buffer.write('</div>\n')

    reset_function_buffer.write(
        f'$("#{{{{form.{flag_name}.id_for_label}}}}").val("{spec.default_value}"); \n')


def create_text_control(flag_name: str, spec: argumenttypes.StringArgument, html_buffer: io.StringIO, reset_function_buffer: io.StringIO):
    """
    Generate HTML for a text input field
    """
    text_control = f'''
        <div class="form-group" data-toggle="tooltip" title="{spec.help_text}">
          <label for="{{{{form.{flag_name}.id_for_label}}}}">{flag_name}</label>
          <input class="form-control" name="{{{{form.{flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}" type="text">
        </div>
    '''

    html_buffer.write(text_control)

    reset_function_buffer.write(
        f'$("#{{{{form.{flag_name}.id_for_label}}}}").val("");\n')


def create_multiselect_control(flag_name: str, spec: argumenttypes.MultipleDiscreteSelection, html_buffer: io.StringIO, reset_function_buffer: io.StringIO):
    """
    Generate HTML for a multiselect choice input field
    """
    # This one is going to be complicated.  For now just set the default values
    # to a text field and don't let the user edit them.
    html_buffer.write(
        f'<div class="form-group" data-toggle="tooltip" title="{spec.help_text}">\n')
    html_buffer.write(f'  <label for="{{{{form.{flag_name}.id_for_label}}}}">{
                      flag_name}</label>\n')

    # Build up the big string of default values
    default_selection = spec.get_toml_value(spec.default_value)
    html_buffer.write(f'  <input class="form-control" type="text" name="{{{{form.{
                      flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}" value="{default_selection}" readonly>\n')
    html_buffer.write('</div>\n')

    reset_function_buffer.write(
        f'$("#{{{{form.{flag_name}.id_for_label}}}}").val({default_selection});\n')


def generate_form_section(section_name: str, arg_spec: dict, html_buffer: io.StringIO, pyform_buffer: io.StringIO, reset_function_buffer: io.StringIO):
    """
    Generate a form section for the given arg spec
    """
    pyform_buffer.write(f'\n    # {section_name}\n')
    reset_function_buffer.write(f'\n// {section_name}\n')
    for flag, spec in arg_spec.items():
        if isinstance(spec, argumenttypes.FlagArg):
            pyform_buffer.write(
                f'    {flag} = forms.BooleanField(required=False)\n')
            create_toggle_control(flag, spec, html_buffer,
                                  reset_function_buffer)
        elif isinstance(spec, argumenttypes.DiscreteNumericalArg):
            if spec.type_fn is int:
                pyform_buffer.write(
                    f'    {flag} = forms.IntegerField(required=False)\n')
            else:
                pyform_buffer.write(
                    f'    {flag} = forms.FloatField(required=False)\n')
            create_slider_control(flag, spec, html_buffer,
                                  reset_function_buffer)
        elif isinstance(spec, argumenttypes.DiscreteCategorialArg):
            # TODO: Be smarter about max_length - 50 should be plenty for now
            pyform_buffer.write(
                f'    {flag} = forms.CharField(max_length=50, required=False)\n')
            create_choice_control(flag, spec, html_buffer,
                                  reset_function_buffer)
        elif isinstance(spec, argumenttypes.MultipleDiscreteSelection):
            pyform_buffer.write(
                # TODO: Revisit max_length
                #       Not sure how big these lists can get
                f'    {flag} = forms.CharField(max_length=5000, required=False)\n')
            # TODO: Just use a text control for now. These
            create_multiselect_control(
                flag, spec, html_buffer, reset_function_buffer)
        elif isinstance(spec, argumenttypes.StringArgument):
            pyform_buffer.write(
                f'    {flag} = forms.CharField(max_length=50, required=False)\n')
            create_text_control(flag, spec, html_buffer, reset_function_buffer)
        elif isinstance(spec, dict):
            # This dictionary contains subsections with their own arg specs
            generate_form_section(flag, spec, html_buffer,
                                  pyform_buffer, reset_function_buffer)
        else:
            print(f'Unknown arg type for {flag}')


def init_pyform(buffer: io.StringIO):
    """
    Add the opening lines to the python form file
    """
    # Handle import and class definition for the Django form
    buffer.write('# Auto-generated code - Do no modify\n')
    buffer.write('from django import forms\n\n')
    buffer.write('class TomlGenForm(forms.Form):\n')


def write_nav_tab_entry(buffer: io.StringIO, section_name: str, active: bool):
    """
    Create an entry on the template page that defines the various form tabs
    """
    active_tab = ' active' if active else ''
    buffer.write(f'  <li class="nav-item"><a class="nav-link{
        active_tab}" data-toggle="tab" href="#options-{
        section_name}">{section_name}</a></li>\n')


def write_tab_page_entry(buffer: io.StringIO, section_name: str, active: bool):
    """
    Add an entry to the top level page containing all of the
    autogenerated form pages.
    """
    active_tab = ' active' if active else ''
    buffer.write(f'<div class="tab-pane fade show{
        active_tab}" id="options-{section_name}">\n')
    buffer.write(
        f'  {{% include "generator/toml_gen/{section_name}.html" %}}\n')
    buffer.write('</div>\n')


def write_instructions_tab(buffer: io.StringIO):
    """
    Create a tab with some basic instructions
    """
    instructions = f'''
        <div>
          <h2>Instructions:</h2>
          <p>
            This form can be used to create or modify settings files for Rando-Dalton Imperial.  The tabs at the top of the form group related settings and all settings in this form start out set to the randomizer default values.  When you have finished adjusting settings to your liking, click the "Generate settings file" button at the bottom of the page to download your toml file.  This file can be used on the <a href="{{% url "generator:index" %}}" target="_blank">generator page</a> to generate a seed.
          </p>
          <p>
            Use the file chooser at the top of the page to load and modify an existing settings file.  The form controls will be updated to reflect the fields in the toml.  The form is not reset when loading a file, so you can load a settings toml and then load a personlization file to combine multiple settings files.  If you want to reset the form, click the "Reset to defaults" button at the bottom of the page.
          </p>
        </div>
    '''

    buffer.write(instructions)


def main():
    pyform_buffer = io.StringIO()
    init_pyform(pyform_buffer)

    nav_tab_buffer = io.StringIO()
    nav_tab_buffer.write('<!--Auto-generated code - Do no modify-->\n')

    tab_page_buffer = io.StringIO()
    tab_page_buffer.write('<!--Auto-generated code - Do no modify-->\n')

    # Build up a reset function for the whole form
    reset_function_buffer = io.StringIO()
    reset_function_buffer.write('''
        <script>
            function reset_to_default() {
    ''')

    html_buffers = {}

    # Create the instructions page and set it as the default tab
    instructions_buffer = io.StringIO()
    write_instructions_tab(instructions_buffer)
    html_buffers['Instructions'] = instructions_buffer
    write_nav_tab_entry(nav_tab_buffer, 'Instructions', True)
    write_tab_page_entry(tab_page_buffer, 'Instructions', True)

    arg_specs = arguments.Settings.get_argument_spec()
    for section_name, arg_spec in arg_specs.items():
        html_buffer = io.StringIO()
        html_buffers[section_name] = html_buffer
        html_buffer.write('<!--Auto-generated code - Do no modify-->\n')
        generate_form_section(section_name, arg_spec,
                              html_buffer, pyform_buffer, reset_function_buffer)

        # Add the nav tab entry for this section
        write_nav_tab_entry(nav_tab_buffer, section_name, False)
        write_tab_page_entry(tab_page_buffer, section_name, False)

    # generatre the Django form
    pyform_buffer.seek(0)
    os.mkdir('form_gen_output')
    with open('form_gen_output/toml_gen_form.py', 'w') as file:
        file.write(pyform_buffer.read())

    # generate html template pages for each option tab
    os.mkdir('form_gen_output/html')
    for name, buffer in html_buffers.items():
        buffer.seek(0)
        with open(f'form_gen_output/html/{name}.html', 'w') as file:
            file.write(buffer.read())

    # Generate the nav tabs template
    nav_tab_buffer.seek(0)
    with open('form_gen_output/html/settings_nav_tabs.html', 'w') as file:
        file.write(nav_tab_buffer.read())

    # generate the tab pages template
    tab_page_buffer.seek(0)
    with open('form_gen_output/html/settings_tab_pages.html', 'w') as file:
        file.write(tab_page_buffer.read())

    reset_function_buffer.write('''
            }
        </script>
    ''')
    reset_function_buffer.seek(0)
    with open('form_gen_output/html/reset_function.html', 'w') as file:
        file.write(reset_function_buffer.read())


if __name__ == "__main__":
    main()
