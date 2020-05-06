from django.http import HttpResponse

# Create your views here.
from django.shortcuts import render
import mysql.connector
import json
import urllib.request
from RIOT_KEY import database_pass
from forms import DropForm

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

    form = DropForm(request.POST or None)
    if form.is_valid():
        blue_jg = form.cleaned_data.get("champ")
        red_jg = form.cleaned_data.get("champ2")

    blue_jg_id = -1
    red_jg_id = -1

    blue_jg_kill_participation = 0
    red_jg_kill_participation = 0

    with OPENER.open(
            "http://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json") as url:
        champ_info = json.loads(url.read().decode())

    # Convert input champion name to champion id
    for o in champ_info:
        if o["name"] == blue_jg:
            blue_jg_id = o["id"]

        elif o["name"] == red_jg:
            red_jg_id = o["id"]

    # Only inspect matches that have both input champions
    sql = "SELECT matchId, participants FROM matches WHERE participants LIKE %s AND participants LIKE %s"
    adr = ("% " + str(blue_jg_id) + ",%", "% " + str(red_jg_id) + ",%")
    CURSOR.execute(sql, adr)
    relevant_matches = CURSOR.fetchall()
    # print(relevant_matches)

    for match in relevant_matches:
        # print(match)
        # Parse participant string
        participants = match[1].split(",")
        stripped = []
        for participant in participants:
            stripped.append(participant.strip())

        # Find player ids from champion ids
        blue_player_id = stripped.index(str(blue_jg_id)) + 1
        red_player_id = stripped.index(str(red_jg_id)) + 1

        # Select all events from this match that involve the death of either blue or red champion
        sql = "SELECT killerId, victimId, assistingParticipantIds FROM events WHERE victimId = %s AND matchId = %s"
        adr = (str(blue_player_id), match[0])
        CURSOR.execute(sql, adr)
        relevant_events = CURSOR.fetchall()

        sql = "SELECT killerId, victimId, assistingParticipantIds FROM events WHERE victimId = %s AND matchId = %s"
        adr = (str(red_player_id), match[0])
        CURSOR.execute(sql, adr)
        relevant_events2 = CURSOR.fetchall()

        relevant_events += relevant_events2
        # print(relevant_events, blue_player_id, red_player_id)

        # Analyze all events that involve the death of either blue or red champion
        for event in relevant_events:
            # print(event)
            # Analyze all champion kills that involve blue or red side jungler
            # event[2] = asssisting champs, event[0] = killer champ
            if str(blue_player_id) in event[2].split(",") or str(blue_player_id) == event[0]:
                blue_jg_kill_participation += 1

            elif str(red_player_id) in event[2].split(",") or str(red_player_id) == event[0]:
                red_jg_kill_participation += 1

    # If no relevant matches, no data
    if blue_jg_kill_participation + red_jg_kill_participation <= 0:
        blue_jg_kill_participation = "0"
        red_jg_kill_participation = "0"
        blue_percentage = "0"
        red_percentage = "0"
        # print("No available data.")
        # return HttpResponse("No available data.")

    else:
        blue_percentage = str(
            blue_jg_kill_participation / (blue_jg_kill_participation + red_jg_kill_participation) * 100)
        red_percentage = str(red_jg_kill_participation / (blue_jg_kill_participation + red_jg_kill_participation) * 100)
    print(blue_jg + " kills " + red_jg + " " + str(blue_jg_kill_participation) + " (" +
          blue_percentage + "%) " + "times before 15 minutes")
    print(red_jg + " kills " + blue_jg + " " + str(red_jg_kill_participation) + " (" +
          red_percentage + "%) " + "times before 15 minutes")
    print("Data is the result of analyzing", len(relevant_matches), "matches.")

    form = DropForm(request.POST or None)
    context = {'form': form, 'submit_action': "", 'blue_jg': blue_jg, 'red_jg': red_jg, 'blue_jg_kp': blue_jg_kill_participation,
               'red_jg_kp': red_jg_kill_participation, 'blue_perc': blue_percentage, 'red_perc': red_percentage,
               'matches': len(relevant_matches),
               'submitbutton': "Submit"}
    return render(request, 'champselect/index.html', context)


def index(request):
    form = DropForm(request.POST or None)

    context = {'form': form, 'submit_action': "success/"}
    return render(request, 'champselect/index.html', context)
