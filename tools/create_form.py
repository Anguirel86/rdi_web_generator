import io

from ctrando.arguments import (
    arguments,
    argumenttypes,
    battlerewards,
    techoptions,
    enemyscaling,
    logicoptions,
    bossrandooptions,
    shopoptions,
    objectiveoptions,
    entranceoptions,
    recruitoptions,
    treasureoptions,
    enemyoptions,
    postrandooptions,
    gearrandooptions,
    characteroptions
)

options_to_omit = []


def create_toggle_control(flag_name: str, default_checked: bool, form_buffer: io.StringIO):
    """
    Generate HTML for a toggle for the given flag.
    """
    default_string = 'checked' if default_checked else ''
    form_buffer.write('<div class="form-group form-check pl-0">\n')
    form_buffer.write(f'  <input type="checkbox" name="{{{{form.{flag_name}.name}}}}" id="{{{{form.{
                      flag_name}.id_for_label}}}}" data-toggle="toggle" {default_string}>\n')
    form_buffer.write(f'  <label for="{{{{form.{flag_name}.id_for_label}}}}">{
                      flag_name}</label>\n')
    form_buffer.write('</div>\n')


def create_slider_control(flag_name: str, min_val, max_val, step, default_val, form_buffer: io.StringIO):
    """
    Generate HTML for a slider with the give min/max/interval
    """
    form_buffer.write('<div class="form-group">\n')
    form_buffer.write(f'  <label for"{{{{form.{
                      flag_name}.id_for_label}}}} class="form-label mr-2">{flag_name}</label>\n')
    form_buffer.write(f'  <input type="range" class="form-range" name="{{{{form.{flag_name}.name}}}}" id="{{{{form.{
                      flag_name}.id_for_label}}}}" min="{min_val}" max="{max_val}" step="{step}" value="{default_val}">\n')
    form_buffer.write(f'  <input type="text" id="{{{{form.{
                      flag_name}.id_for_label}}}}_text" form="none" size="1">\n')
    form_buffer.write('</div>\n')


def create_choice_control(flag_name: str, choices: list, default_value, form_buffer: io.StringIO):
    """
    Generate HTML for a dropdown box for the provided choice list
    """
    form_buffer.write('<div class="form-group">\n')
    form_buffer.write(f'  <label for="{{{{form.{flag_name}.id_for_label}}}}">{
                      flag_name}:</label>\n')
    form_buffer.write(f'  <select class="form-control" name="{{{{form.{
                      flag_name}.name}}}}" id="{{{{form.{flag_name}.id_for_label}}}}">\n')
    for choice in choices:
        selected_string = 'selected' if choice == default_value else ''
        form_buffer.write(f'    <option value="{choice}" {
                          selected_string}>{choice}</option>\n')
    form_buffer.write('  </select>\n')
    form_buffer.write('</div>\n')


def generate_form_section(section_name: str, arg_spec: dict, html_buffer: io.StringIO, pyform_buffer: io.StringIO):
    """
    Generate a form section for the given arg spec
    """
    pyform_buffer.write(f'\n    # {section_name}\n')
    for flag, spec in arg_spec.items():
        if isinstance(spec, argumenttypes.FlagArg):
            pyform_buffer.write(
                f'    {flag} = forms.BooleanField(required=False)\n')
            create_toggle_control(flag, spec.default_value, html_buffer)
        elif isinstance(spec, argumenttypes.DiscreteNumericalArg):
            pyform_buffer.write(
                f'    {flag} = forms.FloatField(required=False)\n')
            create_slider_control(flag, spec.min_value, spec.max_value,
                                  spec.interval, spec.default_value, html_buffer)
        elif isinstance(spec, argumenttypes.DiscreteCategorialArg):
            # TODO: Be smarter about max_length - 50 should be plenty for now
            pyform_buffer.write(
                f'    {flag} = forms.CharField(max_length=50)\n')
            create_choice_control(flag, spec.choices,
                                  spec.default_value, html_buffer)
        elif isinstance(spec, argumenttypes.MultipleDiscreteSelection):
            pyform_buffer.write(
                # TODO: Revisit max_length
                #       Not sure how big these lists can get
                f'    {flag} = forms.CharField(max_length=1000)\n')
            print('Unhandled multiplediscreteselection case')
        elif isinstance(spec, dict):
            # This dictionary contains subsections with their own arg specs
            generate_form_section(flag, spec, html_buffer, pyform_buffer)
        else:
            print(f'Unknown arg type for {flag}')


def main():
    pyform_buffer = io.StringIO()
    html_buffers = {}

    arg_specs = arguments.Settings.get_argument_spec()

    for section_name, arg_spec in arg_specs.items():
        print(f'Generating section {section_name}')
        html_buffer = io.StringIO()
        html_buffers[section_name] = html_buffer

        generate_form_section(section_name, arg_spec,
                              html_buffer, pyform_buffer)

    # Print out the test data
    # html_buffer.seek(0)
    # print(html_buffer.read())

    print('------------------------------------')
    pyform_buffer.seek(0)
    print(pyform_buffer.read())


if __name__ == "__main__":
    main()
