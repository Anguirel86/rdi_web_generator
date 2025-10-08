from django import forms


class GeneratorForm(forms.Form):
    """
    Form class for RDI generator data.
    """
    settings_file = forms.FileField(required=False)
    personalization_file = forms.FileField(required=False)
    preset_file = forms.CharField(max_length=50, required=False)

