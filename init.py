import urllib
import json
import mysql.connector
from riotwatcher import LolWatcher
from RIOT_KEY import get_key
from RIOT_KEY import database_pass

database = mysql.connector.connect(host="localhost", user="root", passwd=database_pass(), database="matches")
CURSOR = database.cursor(buffered=True)
WATCHER = LolWatcher(get_key())

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

if __name__ == "__main__":
    while True:
        main("na1")  # Create database for north american servers