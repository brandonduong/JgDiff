import urllib
import json
import mysql.connector
from riotwatcher import LolWatcher
from RIOT_KEY import get_key
from RIOT_KEY import database_pass


class AppURLopener(urllib.request.FancyURLopener):
    version = "Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11"


database = mysql.connector.connect(host="localhost", user="root", passwd=database_pass(), database="matches")
CURSOR = database.cursor(buffered=True)
WATCHER = LolWatcher(get_key())
OPENER = AppURLopener()


def main(region):
    # Creates database of all needed information from all given matchIds
    # Must run once for every new patch

    # Use fetched Match Ids hosted by canisback
    # Note: Only have for major regions (i.e eun1, euw1, jp1, kr, na1)
    with urllib.request.urlopen("http://canisback.com/matchId/matchlist_" + region + ".json") as url:
        match_ids = json.loads(url.read().decode())

    # Used to skip all that have already been examined
    CURSOR.execute("SELECT matchId FROM matches")
    select = CURSOR.fetchall()
    already_examined = []
    for i in select:
        already_examined.append(i[0])

    num_examined = 0
    for i in match_ids:
        if str(i) in already_examined:  # Skip all matchIds that have already been examined
            continue

        try:
            match = WATCHER.match.by_id(region, i)  # Get match info
            match_timeline = WATCHER.match.timeline_by_match(region, i)  # Get match timeline

        except:
            print("Error")
            return

        participants = []
        for o in match["participants"]:
            participants.append(o["championId"])

        sql = "INSERT IGNORE INTO matches (matchId, participants) VALUES (%s, %s)"
        val = (str(i), " " + ", ".join(map(str, participants)))
        CURSOR.execute(sql, val)
        database.commit()

        counter = 0

        # Get all events that happened in all time frames below 15 minutes (900000 ms)
        while (len(match_timeline["frames"]) > counter and match_timeline["frames"][counter]["timestamp"] < 900000):
            events = match_timeline["frames"][counter]["events"]

            # Analyze all events that happened in all time frames below 15 minutes
            for event in events:
                # Analyze all champion kills
                if event["type"] == "CHAMPION_KILL":
                    killerId = event["killerId"]
                    victimId = event["victimId"]
                    assistingParticipants = event["assistingParticipantIds"]
                    sql = "INSERT INTO events (killerId, victimId, assistingParticipantIds, matchId) VALUES (%s, %s, %s, %s)"
                    val = (killerId, victimId, ",".join(map(str, assistingParticipants)), i)
                    CURSOR.execute(sql, val)
                    database.commit()

            counter += 1

        print("examined: ", num_examined, "matches")
        num_examined += 1

    calculate()

def calculate():
    # Precalculates/updates matchups and stores that information in database

    with OPENER.open(
            "http://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json") as url:
        champ_info = json.loads(url.read().decode())

    # Used to skip all that have already been examined
    CURSOR.execute("SELECT blue_champ, red_champ FROM matchups")
    select = CURSOR.fetchall()
    already_examined = []
    for i in select:
        already_examined.append(i)

    print (already_examined)

    for champ_info_1 in champ_info:
        # champ_info_1["name"]
        blue_jg_id = champ_info_1["id"]

        for champ_info_2 in champ_info:
            # Skip mirror matchups + reverse side matchups (Don't calculate Camille vs Aatrox if Aatrox vs Camille done)
            if champ_info.index(champ_info_2) <= champ_info.index(champ_info_1):
                continue

            # Skipped already calculated matchups
            elif (champ_info_1["name"], champ_info_2["name"]) in already_examined:
                continue

            red_jg_id = champ_info_2["id"]

            red_jg_kill_participation = 0
            blue_jg_kill_participation = 0

            # Only inspect matches that have both input champions
            sql = "SELECT matchId, participants FROM matches WHERE (participants LIKE %s OR participants LIKE %s) AND (participants LIKE %s OR participants LIKE %s)"
            adr = ("% " + str(blue_jg_id) + ",%", "% " + str(blue_jg_id), "% " + str(red_jg_id) + ",%", "% " + str(red_jg_id))
            CURSOR.execute(sql, adr)
            relevant_matches = CURSOR.fetchall()
            # print(relevant_matches)

            relevant_match_counter = 0
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

                # Skip this match if the two champs specified are on the same team
                if not ((blue_player_id <= 5 and red_player_id > 5) or (red_player_id <= 5 and blue_player_id > 5)):
                    continue
                relevant_match_counter += 1

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
                print("No available data.")
                continue

            else:
                blue_percentage = str(
                    blue_jg_kill_participation / (blue_jg_kill_participation + red_jg_kill_participation) * 100)
                red_percentage = str(red_jg_kill_participation / (blue_jg_kill_participation + red_jg_kill_participation) * 100)
                blue_avg = round(blue_jg_kill_participation / relevant_match_counter, 2)
                red_avg = round(red_jg_kill_participation / relevant_match_counter, 2)

            print(champ_info_1["name"] + " kills " + champ_info_2["name"] + " " + str(blue_jg_kill_participation) + " (" +
                  blue_percentage + "%) " + "times before 15 minutes. Average of " + str(
                blue_jg_kill_participation / relevant_match_counter) + " kills per match (before 15 minutes).")
            print(champ_info_2["name"] + " kills " + champ_info_1["name"] + " " + str(red_jg_kill_participation) + " (" +
                  red_percentage + "%) " + "times before 15 minutes. Average of " + str(
                red_jg_kill_participation / relevant_match_counter) + " kills per match (before 15 minutes).")
            print("Data is the result of analyzing", relevant_match_counter, "matches.")

            sql = "INSERT IGNORE INTO matchups (blue_champ, red_champ, blue_kills, red_kills, relevent_matches) VALUES (%s, %s, %s, %s, %s)"
            val = (champ_info_1["name"], champ_info_2["name"], blue_jg_kill_participation, red_jg_kill_participation, relevant_match_counter)
            CURSOR.execute(sql, val)
            database.commit()


if __name__ == "__main__":
    while True:
        main("na1")  # Create database for north american servers
