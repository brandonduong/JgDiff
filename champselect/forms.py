from django.forms import ModelForm
from champselect.models import DropDown


class DropDownForm(ModelForm):
    class Meta:
        model = DropDown
        fields = ["champ", "champ2"]
