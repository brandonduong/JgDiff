from django import forms
import urllib.request
import json


class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11"


OPENER = AppURLopener()
with OPENER.open(
        "http://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json"
) as url:
    champ_info = json.loads(url.read().decode())

CHAMPS = []

# Create list of all champ names for dropdown menu
for o in champ_info:
    CHAMPS.append((o["name"], o["name"]))

CHAMPS.sort()
CHAMPS.remove(("None", "None"))


class DropForm(forms.Form):
    champ = forms.ChoiceField(choices=CHAMPS, label="Blue Side Champion")
    champ2 = forms.ChoiceField(choices=CHAMPS, label="Red Side Champion")
