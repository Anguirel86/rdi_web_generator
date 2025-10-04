# django imports
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from wsgiref.util import FileWrapper

from django.views import View
from django.views.generic import FormView

from .forms import GeneratorForm
from .toml_gen_form import TomlGenForm

# RDI rando imports
import ctrando
import ctrando.randomizer
from ctrando.arguments import tomloptions

# standard lib imports
from importlib import resources as impres
from zipfile import ZipFile
import io
import os
import tempfile
import toml
import tomllib


class IndexView(View):
    """
    Index page with some basic information/links and the generate form
    """

    @classmethod
    def get(cls, request):
        form = GeneratorForm()
        context = {
            'form': form
        }
        return render(request, 'generator/index.html', context)


class TomlFormView(View):
    """
    Main page of the toml generator form
    """
    @classmethod
    def get(cls, request):
        form = TomlGenForm()
        context = {
            'form': form
        }
        return render(request, 'generator/toml_form.html', context)


class TomlGenView(FormView):
    """
    Handle actual TOML generation
    """
    form_class = TomlGenForm

    def form_valid(self, form):

        data_dict = {}
        # Loop over the form fields and store them in a new dictionary
        # Most fields can be read as-is, but the list fields will need to
        # be converted from a string to a list type in the new dict.
        for name, value in form.cleaned_data.items():
            if isinstance(value, str):
                if value.startswith('[') and value.endswith(']'):
                    # If this is an empty list then don't add the field to the toml
                    if len(value) != 2:
                        temp = [x.replace("'", '').strip()
                                for x in value[1:-1].split(',')]
                        data_dict[name] = temp
            else:
                data_dict[name] = value

        # Convert the form fields to TOML
        toml_data = io.StringIO()
        toml.dump(data_dict, toml_data)

        # Feed the toml data to the rando arg parser to validate it
        toml_data.seek(0)
        toml_dict = tomllib.load(io.BytesIO(toml_data.getvalue().encode()))
        try:
            args = tomloptions.toml_data_to_args(toml_dict)
            settings = ctrando.randomizer.extract_settings(*args)
        except ValueError as ve:
            context = {
                'form': form,
                'error_text': str(ve)
            }
            return render(self.request, 'generator/toml_form.html', context)

        # If we made it here, the form is good
        # Package it up and send it to the user as a toml file
        # NOTE: toml content type is application/toml, which implies it's
        #       meant to be read by an application.  Going to use text/plain
        #       for now just to ensure it's treated as a text file in browsers
        toml_data.seek(0)
        content = FileWrapper(toml_data)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=settings.toml'

        return response

    def form_invalid(self, form):
        context = {
            'form': form,
            'error_text': str(form.errors)
        }
        return render(self.request, 'generator/toml_form.html', context)


class GenerateView(FormView):
    """
    Handle generating the seed and providing a patch file
    """
    form_class = GeneratorForm

    def form_valid(self, form):

        # Check is the user selected a preset or uploaded a file
        if len(self.request.FILES) == 0:
            # Preset file
            preset_name = form.cleaned_data['preset_file']
            if preset_name == '':
                # User must provide either a preset name or a settings file
                context = {
                    'form': form,
                    'error_text': f'Select a preset or a custom settings file: {preset_name}'
                }
                return render(self.request, 'generator/index.html', context)

            # Read the preset file from the ctrando package
            preset_file_path = impres.files(
                ctrando) / f'presets/{preset_name}.toml'
            if not os.path.isfile(preset_file_path):
                context = {
                    'form': form,
                    'error_text': f'Invalid preset file: {preset_name}.toml'
                }
                return render(self.request, 'generator/index.html', context)

            # Preset file exists, read it in
            with open(preset_file_path, 'rb') as f:
                buf = io.BytesIO(f.read())

        else:
            # Custom settings file
            # Get the settings file from the form
            buf = io.BytesIO(self.request.FILES['settings_file'].read())

        toml_dict = tomllib.load(buf)
        toml_dict['input_file'] = './ct.sfc'  # TODO: Needed?

        # Generate a randomized ROM
        try:
            args = tomloptions.toml_data_to_args(toml_dict)
            settings = ctrando.randomizer.extract_settings(*args)
            base_rom = ctrando.common.ctrom.CTRom.from_file('./ct.sfc')
            ct_rom = ctrando.randomizer.ctrom.CTRom(base_rom.getvalue())
            config = ctrando.randomizer.get_random_config(settings, ct_rom)
            out_rom = ctrando.randomizer.get_ctrom_from_config(
                ct_rom, settings, config)
        except ValueError as ve:
            context = {
                'form': form,
                'error_text': str(ve)
            }
            return render(self.request, 'generator/index.html', context)

        # Create a patch file
        # python-bps is insanely slow.
        temp_file = tempfile.NamedTemporaryFile()
        bps_file_name = f'{temp_file.file.name}.bps'
        try:
            temp_file.write(out_rom.getbuffer())
            os.system(
                f'flips --create ct.sfc {temp_file.file.name} {bps_file_name}')
        except Exception:
            context = {
                'form': form,
                'error_text': 'Failed to generate patch file'
            }
            return render(self.request, 'generator/index.html', context)

        # Get the spoiler log
        spoiler_file = io.StringIO()
        ctrando.randomizer.write_spoilers_to_file(
            settings, config, spoiler_file)

        # Create a zip file with the patch and spoiler log
        zip_buf = io.BytesIO()

        with ZipFile(zip_buf, 'w') as zip_file:
            # zip_file.writestr('ct-mod.sfc', out_rom.getbuffer())
            zip_file.write(bps_file_name, 'ct-mod.bps')
            zip_file.writestr('ct-mod-spoilers.txt', spoiler_file.getvalue())

        # Clean up the temporary BPS file
        os.remove(bps_file_name)

        zip_buf.seek(0)

        content = FileWrapper(zip_buf)
        response = HttpResponse(
            content, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=ct-mod.zip'

        return response

    def form_invalid(self, form):
        context = {
            'form': form,
            'error_text': 'Choose a preset or upload a settings file.'
        }
        return render(self.request, 'generator/index.html', context)
