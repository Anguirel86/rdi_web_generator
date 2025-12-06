# django imports
from django.shortcuts import render
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
from wsgiref.util import FileWrapper

from django.views import View
from django.views.generic import FormView

from .forms import GeneratorForm
from .toml_gen_form import TomlGenForm

# RDI rando imports
import ctrando
import ctrando.randomizer
from ctrando.arguments import arguments, tomloptions
from ctrando.arguments.postrandooptions import PostRandoOptions

# standard lib imports
import argparse
import importlib.resources
from zipfile import ZipFile
import io
import os
import tempfile
import toml
import tomllib
import traceback
import typing


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


class FetchPresetView(View):
    """
    Fetch a preset (toml) file from the randomizer.
    """

    @classmethod
    def get(cls, request, preset_id):
        # Get the preset file from the randomizer package
        try:
            preset_data = arguments.Presets[preset_id].value
        except KeyError:
            # Invalid preset file
            return HttpResponseNotFound(f'Invalid preset: {preset_id}')

        preset_file = importlib.resources.files(
            'ctrando.arguments.presets').joinpath(preset_data.filename)

        with open(preset_file, 'r') as file:
            return FileResponse(file.read(), filename='preset.toml')


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
                elif len(value) > 0:
                    # All non-list strings.  Skip empty fields
                    data_dict[name] = value
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

    def get_settings_dict(self, form) -> dict[str, typing.Any]:
        """
        Get the settings dictionary corresponding to the user's chosen preset
        or settings file
        """
        has_preset = form.cleaned_data['preset_file'] != ''
        has_settings_file = 'settings_file' in self.request.FILES

        if not has_preset and not has_settings_file:
            # We need at least one of these to continue
            raise ValueError(
                'Select a preset or upload a custom settings file')

        if has_settings_file:
            # Load the user's custom settings file
            buf = io.BytesIO(self.request.FILES['settings_file'].read())
            return tomllib.load(buf)
        else:
            # Get the preset data from the rando
            preset_name = form.cleaned_data['preset_file']
            preset = arguments.Presets[preset_name]
            return arguments.get_preset(preset)

    def get_personalization_settings(self):
        """
        Apply personalization if the user provided a file
        """
        personal_settings = None
        if 'personalization_file' in self.request.FILES:
            buf = io.BytesIO(
                self.request.FILES['personalization_file'].read())

            try:
                personalization_dict = tomllib.load(buf)
            except Exception as ex:
                raise Exception('Invalid personalization file: ' + str(ex))

            personal_opts = tomloptions.toml_data_to_args(personalization_dict)
            personal_parser = argparse.ArgumentParser()
            personal_parser.add_argument_group(
                PostRandoOptions.add_group_to_parser(personal_parser))
            namespace = personal_parser.parse_args(personal_opts)
            personal_settings = PostRandoOptions.extract_from_namespace(
                namespace)

        return personal_settings

    def generate(self, settings_dict, personal_settings):
        """
        Generate a randomized game based on the given settings files
        """
        try:
            args = tomloptions.toml_data_to_args(settings_dict)
            settings = ctrando.randomizer.extract_settings(*args)
            if personal_settings is not None:
                settings.post_random_options = personal_settings
            base_rom = ctrando.common.ctrom.CTRom.from_file('./ct.sfc')
            ct_rom = ctrando.randomizer.ctrom.CTRom(base_rom.getvalue())
            config = ctrando.randomizer.get_random_config(settings, ct_rom)
            out_rom = ctrando.randomizer.get_ctrom_from_config(
                ct_rom, settings, config, 'post_config.pkl', 'prepatched_rom.pkl')

            spoiler_file = io.StringIO()
            ctrando.randomizer.write_spoilers_to_file(
                settings, config, spoiler_file)
        except ValueError as ve:
            raise Exception(f'Invalid args: {str(ve)}')
        except Exception as ex:
            raise Exception(f'Unknown error during generation: {str(ex)}')

        return out_rom, spoiler_file

    def get_patch_file(self, form, out_rom) -> io.BytesIO:
        """
        Get a BytesIO object with the patch file data
        """
        temp_file = tempfile.NamedTemporaryFile()
        bps_file_name = f'{temp_file.file.name}.bps'
        patch_buffer = io.BytesIO()
        try:
            # Write the patch file
            temp_file.write(out_rom.getbuffer())
            os.system(
                f'flips --create ct.sfc {temp_file.file.name} {bps_file_name}')

            # Read the patch file back into a BytesIO object
            with open(bps_file_name, 'rb') as patch_file:
                patch_buffer.write(patch_file.read())

            # Clean up the temp bps file
            os.remove(bps_file_name)

        except Exception as ex:
            raise Exception('Failed to generate patch file: ' + str(ex))

        return patch_buffer

    def form_valid(self, form):

        try:
            # Get the settings for this request
            settings_dict = self.get_settings_dict(form)
            settings_dict['input_file'] = './ct.sfc'  # TODO: Needed?
            personal_settings = self.get_personalization_settings()

            # Generate a randomized ROM
            out_rom, spoiler_log = self.generate(
                settings_dict, personal_settings)

            # Create the patch file
            patch_file = self.get_patch_file(form, out_rom)
        except Exception as ex:
            context = {
                'form': form,
                'error_text': str(ex)
            }
            return render(self.request, 'generator/index.html', context)

        # Build the zip file to send to the user
        zip_buf = io.BytesIO()
        with ZipFile(zip_buf, 'w') as zip_file:
            zip_file.writestr('ct-mod.bps', patch_file.getvalue())
            zip_file.writestr('ct-mod-spoilers.txt', spoiler_log.getvalue())
        zip_buf.seek(0)

        # Build and send the response object
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
