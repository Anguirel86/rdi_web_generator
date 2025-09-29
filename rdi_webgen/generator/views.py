# django imports
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from wsgiref.util import FileWrapper

from django.views import View
from django.views.generic import FormView

from .forms import GeneratorForm


# bps patch imports
from bps.diff import diff_bytearrays
from bps.io import write_bps
from bps.util import bps_progress

# RDI rando imports
import ctrando.randomizer
from ctrando.arguments import tomloptions


# standard lib imports
import io
import tomllib

# Create your views here.


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
        patch_data = io.BytesIO()
        block_size = (len(ct_rom), + len(out_rom) // 100000 + 1)
        iterable = diff_bytearrays(block_size, ct_rom, out_rom)
        write_bps(bps_progress(iterable), patch_data)

        # TODO: Pack the patch in a zip with the spoiler log
        content = FileWrapper(patch_data)
        response = HttpResponse(
            content, content_type='application/octet-stream')
        response['Content-Length'] = len(patch_data)
        response['Content-Disposition'] = 'attachment; filename=ct.bps'

        return response

    def form_invalid(self, form):
        # TODO: Real error page
        return render(self.request, 'generator/error.html', status=404)
