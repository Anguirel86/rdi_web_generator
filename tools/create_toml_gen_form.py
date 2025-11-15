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


class TomlFormAutogen():
    def __init__(self):
        self.pyform_buffer = self._init_pyform()
        self.nav_tab_buffer = self._init_html_buffer()
        self.tab_page_buffer = self._init_html_buffer()
        self.reset_function_buffer = self._init_reset_func_buffer()

        # Dictionary of page names to page buffers
        self.html_buffers = {}

        # create the instructions page
        temp = self._write_instructions_tab()
        self.html_buffers['getting_started'] = temp
        self._write_nav_tab_entry('getting_started', True)
        self._write_tab_page_entry('getting_started', True)

    @staticmethod
    def _init_reset_func_buffer() -> io.StringIO:
        """
        Init the reset function buffer
        """
        buffer = io.StringIO()
        buffer.write('''
            <script>
                function reset_to_default() {

                let status_text = document.getElementById("status_text");
                status_text.innerHTML = "";

        ''')
        return buffer

    @staticmethod
    def _init_html_buffer() -> io.StringIO:
        """
        Create a buffer for an HTML page and add an autogen comment
        """
        buffer = io.StringIO()
        buffer.write('<!--Auto-generated code - Do not modify-->\n')
        return buffer

    @staticmethod
    def _init_pyform() -> io.StringIO:
        """
        Add the opening lines to the python form file
        """
        # Handle import and class definition for the Django form
        buffer = io.StringIO()
        buffer.write('# Auto-generated code - Do not modify\n')
        buffer.write('from django import forms\n\n')
        buffer.write('class TomlGenForm(forms.Form):\n')
        return buffer

    @staticmethod
    def sanitize_string(input: str) -> str:
        """
        Sanitize a string so it can be used in an html document
        """
        output = input.replace('"', '&quot;')
        return output

    @staticmethod
    def get_display_name(name: str) -> str:
        return name.replace('_', ' ').title()

    def _create_toggle_control(
            self,
            flag_name: str,
            spec: argumenttypes.FlagArg,
            html_buffer: io.StringIO):
        """
        Generate HTML for a toggle for the given flag.
        """
        default_string = 'checked' if spec.default_value else ''
        help_text = self.sanitize_string(spec.help_text)
        display_name = self.get_display_name(flag_name)
        toggle_control = f'''
            <div class="form-group form-check pl-0" data-toggle="tooltip" title="{help_text}">
              <input type="checkbox" name="{{{{form.{flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}" data-toggle="toggle" {default_string}>
              <label for="{{{{form.{flag_name}.id_for_label}}}}">{display_name}</label>
            </div>
        '''
        html_buffer.write(toggle_control)

        default_val = 'true' if spec.default_value else 'false'
        self.reset_function_buffer.write(
            f'$("#{{{{form.{flag_name}.id_for_label}}}}").prop("checked", {default_val}).change();\n')

    def _create_slider_control(
            self,
            flag_name: str,
            spec: argumenttypes.DiscreteNumericalArg,
            html_buffer: io.StringIO):
        """
        Generate HTML for a slider with the give min/max/interval
        """
        # The slider and text box should update each other on change
        help_text = self.sanitize_string(spec.help_text)
        display_name = self.get_display_name(flag_name)
        slider_control = f'''
            <div class="form-group" data-toggle="tooltip" title="{help_text}">
              <label for="{{{{form.{flag_name}.id_for_label}}}}" class="form-label mr-2">{display_name}</label>
              <input type="range" class="form-range" name="{{{{form.{flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}" min="{spec.min_value}" max="{spec.max_value}" step="{spec.interval}" value="{spec.default_value}">
              <input type="text" id="{{{{form.{flag_name}.id_for_label}}}}_text" form="none" size="2" value="{spec.default_value}">
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

        html_buffer.write(slider_control)

        self.reset_function_buffer.write(
            f'$("#{{{{form.{flag_name}.id_for_label}}}}").val({spec.default_value}).change();\n')

        self.reset_function_buffer.write(
            f'$("#{{{{form.{flag_name}.id_for_label}}}}_text").val({spec.default_value}).change();\n')

    def _create_choice_control(
            self,
            flag_name: str,
            spec: argumenttypes.DiscreteCategorialArg,
            html_buffer: io.StringIO):
        """
        Generate HTML for a dropdown box for the provided choice list
        """
        help_text = self.sanitize_string(spec.help_text)
        display_name = self.get_display_name(flag_name)
        html_buffer.write(f'''
            <div class="form-group" data-toggle="tooltip" title="{help_text}">
                <label for="{{{{form.{flag_name}.id_for_label}}}}">{display_name}:</label>
                <select class="form-control" name="{{{{form.{flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}">
        ''')
        for choice in spec.choices:
            selected_string = 'selected' if choice == spec.default_value else ''
            html_buffer.write(f'    <option value="{choice}" {
                selected_string}>{choice}</option>\n')
        html_buffer.write('  </select>\n')
        html_buffer.write('</div>\n')

        self.reset_function_buffer.write(
            f'$("#{{{{form.{flag_name}.id_for_label}}}}").val("{spec.default_value}"); \n')

    def _create_text_control(
            self,
            flag_name: str,
            spec: argumenttypes.StringArgument,
            html_buffer: io.StringIO):
        """
        Generate HTML for a text input field
        """
        help_text = self.sanitize_string(spec.help_text)
        display_name = self.get_display_name(flag_name)
        text_control = f'''
            <div class="form-group" data-toggle="tooltip" title="{help_text}">
              <label for="{{{{form.{flag_name}.id_for_label}}}}">{display_name}</label>
              <input class="form-control" name="{{{{form.{flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}" type="text">
            </div>
        '''

        html_buffer.write(text_control)

        self.reset_function_buffer.write(
            f'$("#{{{{form.{flag_name}.id_for_label}}}}").val("");\n')

    def _create_multiselect_control(
            self,
            flag_name: str,
            spec: argumenttypes.MultipleDiscreteSelection,
            html_buffer: io.StringIO):
        """
        Generate HTML for a multiselect choice input field
        """
        help_text = self.sanitize_string(spec.help_text)
        display_name = self.get_display_name(flag_name)
        searchbox_id = f'{flag_name}_searchbox'
        src_list_id = f'{flag_name}_srclist'
        dest_list_id = f'{flag_name}_destlist'

        # Build up strings for the source/dest list elements
        src_elems = io.StringIO()
        dest_elems = io.StringIO()

        # Default values for resetting form fields
        default_selection = io.StringIO()
        default_form_data = io.StringIO()

        first_elem = True
        for elem in spec.choices:
            if elem not in spec.default_value:
                name = spec.str_from_choice_fn(elem)
                src_elems.write(f'<span id="{flag_name}_{
                    name}" class="movable border border-secondary rounded pl-1 pr-1">{name}</span>\n')

        default_form_data.write('[')
        first_elem = True
        for elem in spec.default_value:
            name = spec.str_from_choice_fn(elem)
            dest_elems.write(f'<span id="{flag_name}_{
                name}" class="movable border border-secondary rounded pl-1 pr-1">{name}</span>\n')

            if not first_elem:
                default_selection.write(',')
                default_form_data.write(',')
            default_selection.write(flag_name + '_' + name)
            default_form_data.write(name)
            first_elem = False

        default_form_data.write(']')

        select_control = f'''
            <label data-toggle="tooltip" title="{help_text}">{display_name}:</label>
            <div class="border border-primary rounded mb-4 pl-2 pr-2">
                <div  class="mt-1" data-toggle="tooltip" title="{help_text}">
                    <label for="{searchbox_id}">Search/Filter</label>
                    <input type="text" id="{searchbox_id}" form="none" name="{searchbox_id}">
                </div>

                <label>Possible:</label>
                <div id="{src_list_id}" style="min-height: 25px; display: flex; flex-wrap: wrap;" class="border border-secondary rounded mb-2">
                    {src_elems.getvalue()}
                </div>
                <label>Selected:</label>
                <div id="{dest_list_id}" style="min-height: 25px; display: flex; flex-wrap: wrap;" class="border border-secondary rounded mb-2">
                    {dest_elems.getvalue()}
                </div>
            </div>
            <input type="hidden" id="{{{{form.{flag_name}.id_for_label}}}}" name="{{{{form.{flag_name}.name}}}}" value="{default_form_data.getvalue()}">
            <script>
                addSelectionListListeners(
                    "{src_list_id}", "{dest_list_id}", "{searchbox_id}", "{{{{form.{flag_name}.id_for_label}}}}");
            </script>
        '''

        html_buffer.write(select_control)

        self.reset_function_buffer.write(
            f'$("#{{{{form.{flag_name}.id_for_label}}}}").val("{default_form_data.getvalue()}");\n')
        self.reset_function_buffer.write(
            f'resetMultiSelectList("{src_list_id}", "{dest_list_id}", "{default_selection.getvalue()}");\n')

    def _create_multiselect_control_temp(
            self,
            flag_name: str,
            spec: argumenttypes.MultipleDiscreteSelection,
            html_buffer: io.StringIO):
        """
        Generate HTML for a multiselect choice input field
        """
        # This one is going to be complicated.  For now just set the default values
        # to a text field and don't let the user edit them.
        help_text = self.sanitize_string(spec.help_text)
        html_buffer.write(
            f'<div class="form-group" data-toggle="tooltip" title="{help_text}">\n')
        html_buffer.write(f'  <label for="{{{{form.{flag_name}.id_for_label}}}}">{
                          flag_name}</label>\n')

        # Build up the big string of default values
        default_selection = spec.get_toml_value(spec.default_value)
        html_buffer.write(f'  <input class="form-control" type="text" name="{{{{form.{
                          flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}" value="{default_selection}" readonly>\n')
        html_buffer.write('</div>\n')

        self.reset_function_buffer.write(
            f'$("#{{{{form.{flag_name}.id_for_label}}}}").val({default_selection});\n')

    @staticmethod
    def _write_instructions_tab() -> io.StringIO:
        """
        oreate the instructions/getting started tab
        Includes basic usage instructions and controls to load presets/files
        """
        buffer = io.StringIO()
        instructions = '''
            <div>
              <h2>Instructions:</h2>
              <p>
                This form can be used to create or modify settings files for Rando-Dalton Imperial.  The tabs at the top of the form group related settings and all settings in this form start out set to the randomizer default values.  When you have finished adjusting settings to your liking, click the "Generate settings file" button at the bottom of the page to download your toml file.  This file can be used on the <a href="{% url "generator:index" %}" target="_blank">generator page</a> to generate a seed.
              </p>
              <p>
                Use the preset buttons or file chooser below to load existing settings.  The form controls will be updated to reflect the fields in the chosen preset/file.  The form is not reset when doing this, so you can load a preset or settings file and then load a personlization file to combine multiple settings files.  If you want to reset the form, click the "Reset to defaults" button at the bottom of the page.
              </p>

              <div class="border border-secondary rounded">
                <label class="form-label ml-2 pt-2" for="id_existing_toml">Load a preset or a toml file</label>
                <div>
                  {% include "generator/toml_gen/preset_buttons.html" %}
                </div>
                <input type="file" class="form-control" id="id_existing_toml" form="none">
              </div>
              <div>
                <h4 id="status_text" style="color: green"></h4>
              </div>
            </div>
        '''
        buffer.write(instructions)

        return buffer

    def generate_form_section(
            self,
            section_name: str,
            arg_spec: dict):
        """
        Generate a form section for the given arg spec
        """
        # Create a page buffer for this section if one doesn't exist
        if section_name not in self.html_buffers:
            html_buffer = self._init_html_buffer()
            self.html_buffers[section_name] = html_buffer
            self._write_nav_tab_entry(section_name, False)
            self._write_tab_page_entry(section_name, False)
        else:
            html_buffer = self.html_buffers[section_name]

        self.pyform_buffer.write(f'\n    # {section_name}\n')
        self.reset_function_buffer.write(f'\n// {section_name}\n')
        for flag, spec in arg_spec.items():
            if isinstance(spec, argumenttypes.FlagArg):
                self.pyform_buffer.write(
                    f'    {flag} = forms.BooleanField(required=False)\n')
                self._create_toggle_control(flag, spec, html_buffer)
            elif isinstance(spec, argumenttypes.DiscreteNumericalArg):
                if spec.type_fn is int:
                    self.pyform_buffer.write(
                        f'    {flag} = forms.IntegerField(required=False)\n')
                else:
                    self.pyform_buffer.write(
                        f'    {flag} = forms.FloatField(required=False)\n')
                self._create_slider_control(flag, spec, html_buffer)
            elif isinstance(spec, argumenttypes.DiscreteCategorialArg):
                # TODO: Be smarter about max_length
                self.pyform_buffer.write(
                    f'    {flag} = forms.CharField(max_length=50, required=False)\n')
                self._create_choice_control(flag, spec, html_buffer)
            elif isinstance(spec, argumenttypes.MultipleDiscreteSelection):
                self.pyform_buffer.write(
                    # TODO: Revisit max_length
                    #       Not sure how big these lists can get
                    f'    {flag} = forms.CharField(max_length=5000, required=False)\n')
                self._create_multiselect_control(
                    flag, spec, html_buffer)
            elif isinstance(spec, argumenttypes.StringArgument):
                # TODO: Be smarter about max_length
                #       Palletes can be 84, so 100 should be ok for now
                self.pyform_buffer.write(
                    f'    {flag} = forms.CharField(max_length=100, required=False)\n')
                self._create_text_control(flag, spec, html_buffer)
            elif isinstance(spec, dict):
                # This dictionary contains subsections with their own arg specs
                self.generate_form_section(section_name, spec)
            else:
                print(f'Unknown arg type for {flag}')

    def _write_nav_tab_entry(self, section_name: str, active: bool):
        """
        Create an entry on the template page that defines the various form tabs
        """
        display_name = self.get_display_name(section_name)

        active_tab = ' active' if active else ''
        self.nav_tab_buffer.write(f'  <li class="nav-item"><a class="nav-link{
            active_tab}" data-toggle="tab" href="#options-{
            section_name}">{display_name}</a></li>\n')

    def _write_tab_page_entry(self, section_name: str, active: bool):
        """
        Add an entry to the top level page containing all of the
        autogenerated form pages.
        """
        active_tab = ' active' if active else ''
        self.tab_page_buffer.write(f'''
            <div class="tab-pane fade show{active_tab}" id="options-{section_name}">
              {{% include "generator/toml_gen/{section_name}.html" %}}
            </div>
        ''')

    def finalize_and_write_pages(self):
        """
        Finalize the page buffers and write everything to disk
        """
        # generatre the Django form
        self.pyform_buffer.seek(0)
        os.mkdir('form_gen_output')
        with open('form_gen_output/toml_gen_form.py', 'w') as file:
            file.write(self.pyform_buffer.read())

        # generate html template pages for each option tab
        os.mkdir('form_gen_output/html')
        for name, buffer in self.html_buffers.items():
            buffer.seek(0)
            with open(f'form_gen_output/html/{name}.html', 'w') as file:
                file.write(buffer.read())

        # Generate the nav tabs template
        self.nav_tab_buffer.seek(0)
        with open('form_gen_output/html/settings_nav_tabs.html', 'w') as file:
            file.write(self.nav_tab_buffer.read())

        # generate the tab pages template
        self.tab_page_buffer.seek(0)
        with open('form_gen_output/html/settings_tab_pages.html', 'w') as file:
            file.write(self.tab_page_buffer.read())

        self.reset_function_buffer.write('''
                }
            </script>
        ''')
        self.reset_function_buffer.seek(0)
        with open('form_gen_output/html/reset_function.html', 'w') as file:
            file.write(self.reset_function_buffer.read())


def main():

    autogen = TomlFormAutogen()

    # Loop the arg specs and write a tab page for each argument grouping
    arg_specs = arguments.Settings.get_argument_spec()
    for section_name, arg_spec in arg_specs.items():
        autogen.generate_form_section(section_name, arg_spec)

    autogen.finalize_and_write_pages()


if __name__ == "__main__":
    main()
