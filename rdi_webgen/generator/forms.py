from django import forms


class GeneratorForm(forms.Form):
    """
    Form class for RDI generator data.
    """
    settings_file = forms.FileField(required=True)
