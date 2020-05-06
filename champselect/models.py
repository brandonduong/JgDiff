from django.db import models
from django.utils import timezone
import urllib
import urllib.request
import json
import datetime


# Create your models here.
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.question_text

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


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

class DropDown(models.Model):
    champ = models.CharField(max_length=25, choices=CHAMPS, default='Aatrox')
    champ2 = models.CharField(max_length=25, choices=CHAMPS, default='Ahri')

    def __str__(self):
        return self.champ, self.champ2
