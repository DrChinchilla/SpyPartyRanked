import os
import gzip
from ReplayParser import * ##Import parse function
def read_log(log_name):
    
   import os
import gzip
import json
import requests

URL = "https://f0t66fsfkd.execute-api.us-east-2.amazonaws.com/default/receive_game_data"

from ReplayParser import * ##Import parse function
def read_log(log_name):
    print("Read log initialized")
    replay_list = []
    match_dict = {}
    ranked_is_on = False
    matches_parsed = 0
    try:
        with gzip.open(log_name, 'rt') as file:
            print("File opened")
            log_lines = file.readlines()
            for line in log_lines:
                if line.count("Ranked Mode On") == 1 and line.count("LobbyClient sending chat message") == 1: ##Turns on ranked when key phrase is found in local chat logs
                    ranked_is_on = True
                    print("Ranked is on")
                elif ranked_is_on == True and line.count("LobbyClient starting to lobby from IN_MATCH") == 1: ##Turns off ranked when match ends
                    ranked_is_on = False
                    print("Ranked is off")
                    matches_parsed += 1
                    match_dict['Match' + str(matches_parsed)] = replay_list #Adds the replay list from the parsed match to the match dictionary to dilineate from other matches in the same log.
                    replay_list = [] #Clears replay log for other matches.       
                elif ranked_is_on == True and line.count("Writing replay") == 1: ##Finds and saves replay paths while ranked is on
                    replay_find = line.split(": ")
                    path_string = replay_find[2]
                    path_string = path_string.rstrip()
                    path_string = path_string.strip('\"')
                    replay_list.append(path_string) 
                    print("Found replay, saving path")
            file.close
            return match_dict
    except:
        print("SpyParty is running!")
        return {}

def get_data(replay_path):
    replay_data = {}
    hummus = ReplayParser()
    replay = hummus.parse(replay_path)
    replay_data['uuid'] = replay.uuid
    replay_data['date'] = replay.date
    replay_data['spy_display'] = replay.spy
    replay_data['spy_user'] = replay.spy_username
    replay_data['sniper_display'] = replay.sniper
    replay_data['sniper_user'] = replay.sniper_username
    replay_data['result'] = replay.result
    replay_data['setup'] = replay.setup
    replay_data['venue'] = replay.venue
    replay_data['variant'] = replay.variant
    replay_data['guests'] = replay.guests
    replay_data['clock'] = replay.clock
    replay_data['duration'] = replay.duration
    replay_data['selected_missions'] = replay.selected_missions
    replay_data['completed_missions'] = replay.completed_missions
    if replay.picked_missions != None:
        replay_data['picked_missions'] = replay.picked_missions
    return(replay_data)

def find_log_path():
    Dir = os.getcwd()
    parent_dir = os.path.dirname(Dir)
    return(parent_dir + "\\logs")

def find_log(log_path):
    last_edited = 0
    log_file = ""
    for file in os.scandir(log_path):
        if os.path.getctime(file) > last_edited:
            last_edited = os.path.getctime(file)
            log_file = os.path.join(log_path, file)
    return log_file

def format_match(match_data):
    formatted_match = {}
    formatted_match['match_id'] = match_data[0]['uuid']
    formatted_match['player_1_id'] = match_data[0]['sniper_user']
    formatted_match['player_1_display'] = match_data[0]['sniper_display']
    formatted_match['player_2_id'] = match_data[0]['spy_user']
    formatted_match['player_2_display'] = match_data[0]['spy_display']
    formatted_match['player_1_totalscore'] = 0
    formatted_match['player_2_totalscore'] = 0
    for game in match_data:
        venue = game['venue']
        venue_played = False
        for key in formatted_match.keys():
            if venue == key:
                venue_played = True
        if venue_played == False:
            formatted_match[venue] = {}
            formatted_match[venue]['player_1_score'] = 0
            formatted_match[venue]['player_2_score'] = 0
        sniper = game['sniper_user']
        spy = game ['spy_user']
        if game['result'] == 'Spy Shot' or 'Time Out':
            if sniper == formatted_match['player_1_id']:
                formatted_match[venue]['player_1_score'] += 1
                formatted_match['player_1_totalscore'] += 1
            elif sniper == formatted_match['player_2_id']:
                formatted_match[venue]['player_2_score'] += 1
                formatted_match['player_2_totalscore'] += 1
        elif game['result'] == 'Missions Win' or 'Civilian Shot':
            if spy == formatted_match['player_1_id']:
                formatted_match[venue]['player_1_score'] += 1
                formatted_match['player_1_totalscore'] += 1
            elif spy == formatted_match['player_2_id']:
                formatted_match[venue]['player_2_score'] += 1
                formatted_match['player_2_totalscore'] += 1
    return formatted_match
###
parent_dir = find_log_path()
print(parent_dir)
recent_log = ''
log_path = find_log(parent_dir) #Beginning of loop set to run every 15 seconds
print(log_path)
if log_path != recent_log:    
    match_dict = read_log(log_path)#Remember to implement not doing this if the log has already been read previously
    print(match_dict)
    if match_dict != {}:
        for game_list in match_dict.values():
            replay_index = 0
            for replay in game_list:
                game_list[replay_index] = get_data(replay)
                replay_index += 1
            print(game_list)
        print(match_dict)
        for game_list in match_dict.values():
            for game in game_list:
                r = requests.post(url = URL, params = {'report_type':'game_result'}, data = game)
                print(r)
            formatted_match = format_match(game_list)
            r = requests.post(url = URL, params = {'report_type':'match_result'}, data = formatted_match)
        log_path = recent_log
