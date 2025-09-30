# django imports
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from wsgiref.util import FileWrapper

from django.views import View
from django.views.generic import FormView

from .forms import GeneratorForm

# RDI rando imports
import ctrando.randomizer
from ctrando.arguments import tomloptions

# standard lib imports
from zipfile import ZipFile
import io
import os
import tempfile
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


class GenerateView(FormView):
    """
    Handle generating the seed and providing a patch file
    """
    form_class = GeneratorForm

    def form_valid(self, form):

        # Get the settings file from the form
        buf = io.BytesIO(self.request.FILES['settings_file'].read())
        toml_dict = tomllib.load(buf)
        toml_dict['input_file'] = './ct.sfc'  # TODO: Needed?

        # Generate a randomized ROM
        args = tomloptions.toml_data_to_args(toml_dict)
        settings = ctrando.randomizer.extract_settings(*args)
        base_rom = ctrando.common.ctrom.CTRom.from_file('./ct.sfc')
        ct_rom = ctrando.randomizer.ctrom.CTRom(base_rom.getvalue())
        config = ctrando.randomizer.get_random_config(settings, ct_rom)
        out_rom = ctrando.randomizer.get_ctrom_from_config(
            ct_rom, settings, config)

        # Create a patch file
        # python-bps is insanely slow.
        temp_file = tempfile.NamedTemporaryFile()
        bps_file_name = f'{temp_file.file.name}.bps'
        try:
            temp_file.write(out_rom.getbuffer())
            os.system(
                f'flips --create ct.sfc {temp_file.file.name} {bps_file_name}')
        except Exception:
            return render(self.request, 'generator/error.html', status=404)

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
        # TODO: Real error page
        return render(self.request, 'generator/error.html', status=404)
