from django.http import HttpResponse

# Create your views here.
from django.shortcuts import render
import mysql.connector
import json
import urllib.request
from .RIOT_KEY import database_pass
from .forms import DropForm

def detail(request, question_id):
    return HttpResponse("You're looking at question %s" % question_id)


def results(request, question_id):
    return HttpResponse("You're looking at the results of question %s" % question_id)


def vote(request, question_id):
    return HttpResponse("You're voting on question %s" % question_id)


class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11"


def calculate(request):
    # region = input("What region to analyze? (br1, eun1, na1, etc.) : ")
    # tier = input("What tier to analyze? (DIAMOND, GOLD, etc.) : ")
    # division = input("What division to analyze? (I, II, III, etc.) : ")
    # queue = "RANKED_SOLO_5x5"
    # Global Variables
    # WATCHER = LolWatcher(get_key())
    # REGIONS = ["br1", "eun1", "euw1", "jp1", "kr", "la1", "la2", "na1", "oc1", "ru", "tr1"]
    OPENER = AppURLopener()
    database = mysql.connector.connect(host="localhost", user="root", passwd=database_pass(), database="matches")
    CURSOR = database.cursor(buffered=True)

    blue_jg = ""
    red_jg = ""
    form = DropForm(request.POST or None)
    if form.is_valid():
        blue_jg = form.cleaned_data.get("champ")
        red_jg = form.cleaned_data.get("champ2")

    sql = "SELECT * from matchups WHERE blue_champ = %s AND red_champ = %s"
    adr = (blue_jg, red_jg)
    CURSOR.execute(sql, adr)
    matchup_data = CURSOR.fetchall()

    # If no data, try flipping champ sides
    if not matchup_data:
        tmp = red_jg
        red_jg = blue_jg
        blue_jg = tmp

        sql = "SELECT * from matchups WHERE blue_champ = %s AND red_champ = %s"
        adr = (blue_jg, red_jg)
        CURSOR.execute(sql, adr)
        matchup_data = CURSOR.fetchall()

    print(matchup_data)

    blue_jg_kill_participation = int(matchup_data[0][2])
    red_jg_kill_participation = int(matchup_data[0][3])
    relevant_match_counter = int(matchup_data[0][4])

    try:
        blue_percentage = str(
            blue_jg_kill_participation / (blue_jg_kill_participation + red_jg_kill_participation) * 100)
        red_percentage = str(red_jg_kill_participation / (blue_jg_kill_participation + red_jg_kill_participation) * 100)
        blue_avg = round(blue_jg_kill_participation/relevant_match_counter, 2)
        red_avg = round(red_jg_kill_participation/relevant_match_counter, 2)

    except:
        blue_percentage = "0"
        red_percentage = "0"
        blue_avg = 0
        red_avg = 0

    print(blue_jg + " kills " + red_jg + " " + str(blue_jg_kill_participation) + " (" +
          blue_percentage + "%) " + "times before 15 minutes. Average of " + str(blue_avg) + " kills per match (before 15 minutes).")
    print(red_jg + " kills " + blue_jg + " " + str(red_jg_kill_participation) + " (" +
          red_percentage + "%) " + "times before 15 minutes. Average of " + str(blue_avg) + " kills per match (before 15 minutes).")
    print("Data is the result of analyzing", relevant_match_counter, "matches.")

    form = DropForm(request.POST or None)
    context = {'form': form, 'submit_action': "", 'blue_jg': blue_jg, 'red_jg': red_jg, 'blue_jg_kp': blue_jg_kill_participation,
               'red_jg_kp': red_jg_kill_participation, 'blue_perc': round(float(blue_percentage), 2), 'red_perc': round(float(red_percentage),2),
               'blue_avg': blue_avg, 'red_avg': red_avg,
               'matches': relevant_match_counter,
               'submitbutton': "Submit"}

    return render(request, 'champselect/index.html', context)


def index(request):
    form = DropForm(request.POST or None)

    context = {'form': form, 'submit_action': "success/"}
    return render(request, 'champselect/index.html', context)
