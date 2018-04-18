import requests
import json
import sqlite3
import csv
from bs4 import BeautifulSoup
import datetime

API_KEY = 'q5zcej3vdue2yamtbu73zf4n'
DBNAME = 'nflquarterbacks.db'
QBCACHE = 'qbcache.json'
TEAMCACHE = 'teamcache.json'

name_id = {}
counter = 1

def init_db():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = '''
        DROP TABLE IF EXISTS 'PlayerInfo';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        CREATE TABLE 'PlayerInfo' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Name' TEXT,
            'NameID' INTEGER,
            'YearBorn' TEXT,
            'College' TEXT,
            'Team' TEXT
        );
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        DROP TABLE IF EXISTS 'SeasonalStats';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        CREATE TABLE 'SeasonalStats' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Name' TEXT,
            'NameId' INTEGER,
            'Team' TEXT,
            'Year' TEXT,
            'Age' TEXT,
            'SeasonRecord' TEXT,
            'Completions' TEXT,
            'PassYards' TEXT,
            'Touchdowns' TEXT,
            'Interceptions' TEXT,
            'Rating' TEXT
        );
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        DROP TABLE IF EXISTS 'Teams';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        CREATE TABLE 'Teams' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'TeamName' TEXT,
            'TeamId' TEXT,
            'Location' TEXT,
            'Stadium' TEXT,
            'Division' TEXT
        );
    '''
    cur.execute(statement)
    conn.commit()

    conn.close()




#Get QB Data and make a cache for data from https://www.pro-football-reference.com/players/qbindex.htm

try:
    cache_file = open(QBCACHE, 'r')
    cache_contents = cache_file.read()
    QB_CACHE_DICT = json.loads(cache_contents)
    cache_file.close()
except:
    QB_CACHE_DICT = {}
def cache_QB_data(baseurl):
    unique_ident = baseurl
    if unique_ident in QB_CACHE_DICT:
        return QB_CACHE_DICT[unique_ident]
    else:
        response = requests.get(baseurl)
        QB_CACHE_DICT[unique_ident] = response.text
        f = open(QBCACHE, 'w')
        dumped_json = json.dumps(QB_CACHE_DICT)
        f.write(dumped_json)
        f.close()
        return QB_CACHE_DICT[unique_ident]


    


def get_QB_data(name):
    page_html = cache_QB_data('https://www.pro-football-reference.com/players/qbindex.htm')
    page_soup = BeautifulSoup(page_html, 'html.parser')
    data = page_soup.find(id='div_players')
    moredata = data.find('tbody')
    qb_data = moredata.find_all('tr')
    qb_dict = {}
    for qb in qb_data:
        qb_name = qb.find('a').string
        ext_link = qb.find('a')['href']
        qb_dict[qb_name] = ext_link
    if name in qb_dict.keys():
        qb_html = cache_QB_data('https://www.pro-football-reference.com/{}'.format(qb_dict[name]))
        qb_soup = BeautifulSoup(qb_html, 'html.parser')
        #print('working')
        #Get player info first
        player_info = qb_soup.find(itemtype='https://schema.org/Person')
        #Get name
        player_name = player_info.find(itemprop='name').string #################
        #Get year born
        ptags = player_info.find_all('p') #################
        for p in ptags:
            if 'Born' in p.text:
                year_born = p.find('span')['data-birth'][0:4]
        #Get teams
        #Get College
        ptags = player_info.find_all('p')
        for p in ptags:
            if 'College' in p.text:
                college = p.find('a').text #################
        #Get teams played on
        passing_info = qb_soup.find(id='passing')
        passing_table = passing_info.find('tbody')
        table_elements = passing_table.find_all('tr')
        player_teams = [] ######################
        return_list = []
        for tr in table_elements:
            td_list = tr.find_all('td', attrs={'data-stat': 'team'})
            for td in td_list:
                if td.string not in player_teams:
                    player_teams.append(td.string)
        for team in player_teams:
            return_list.append((player_name, year_born, college, team))
        return return_list
    else:
        return 'not a QB name'


def populate_PlayerInfo(list_of_tuples):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    global name_id
    global counter
    for player in list_of_tuples:
        player_name = player[0]
        if player_name not in name_id.keys():
            name_id[player_name] = counter
            counter += 1
        year_born = player[1]
        college = player[2]
        team = player[3]

        insertion = (None, player_name, name_id[player_name], year_born, college, team)
        statement = '''
            INSERT INTO 'PlayerInfo'
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        cur.execute(statement, insertion)
        conn.commit()
    conn.close()

#print(get_QB_data('Tom Brady'))


def get_season_data(name): #this should be the return value of  get_QB_data
    page_html = cache_QB_data('https://www.pro-football-reference.com/players/qbindex.htm')
    page_soup = BeautifulSoup(page_html, 'html.parser')
    data = page_soup.find(id='div_players')
    moredata = data.find('tbody')
    qb_data = moredata.find_all('tr')
    qb_dict = {}
    for qb in qb_data:
        qb_name = qb.find('a').string
        ext_link = qb.find('a')['href']
        if qb_name not in qb_dict.keys():
            qb_dict[qb_name] = ext_link
    if name in qb_dict.keys():
        qb_html = cache_QB_data('https://www.pro-football-reference.com/{}'.format(qb_dict[name]))
        qb_soup = BeautifulSoup(qb_html, 'html.parser')
        passing_table_html = qb_soup.find(id='passing')
        passing_table_rows = passing_table_html.find_all(class_='full_table')
        info_list = []
        for row in passing_table_rows:
            year = row.find(attrs={'data-stat': 'year_id'}).text[0:4]
            age = row.find(attrs={'data-stat': 'age'}).string
            team = row.find(attrs={'data-stat': 'team'}).string
            record = row.find(attrs={'data-stat': 'qb_rec'}).string
            comp_percent = row.find(attrs={'data-stat': 'pass_cmp_perc'}).string
            pass_yards = row.find(attrs={'data-stat': 'pass_yds'}).string
            passing_tds = row.find(attrs={'data-stat': 'pass_td'}).string
            interceptions = row.find(attrs={'data-stat': 'pass_int'}).string
            qbr = row.find(attrs={'data-stat': 'qbr'}).string
            info = (name, year, age, team, record, comp_percent, pass_yards, passing_tds, interceptions, qbr)
            info_list.append(info)
        return info_list
    else:
        return 'not a name'

#print(get_season_data('Peyton Manning'))

def populate_SeasonalStats(list_of_tuples):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    global name_id
    global counter
    for season in list_of_tuples:
        player_name = season[0]#
        year = season[1]
        player_age = season[2]
        team = season[3]#
        record = season[4]
        comp_percent = season[5]
        pass_yards = season[6]
        passing_tds = season[7]
        interceptions = season[8]


        if player_name not in name_id.keys():
            name_id[player_name] = counter
            counter += 1
        playeridnum = name_id[player_name]

        qbr = season[9]
        insertion = (None, player_name, playeridnum, team, year, player_age, record, comp_percent, pass_yards, passing_tds, interceptions, qbr)
        statement = '''
            INSERT INTO 'SeasonalStats'
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        cur.execute(statement, insertion)
        conn.commit()
    conn.close()


try:
    cache_file = open(TEAMCACHE, 'r')
    cache_contents = cache_file.read()
    TEAM_CACHE_DICT = json.loads(cache_contents)
    cache_file.close()
except:
    TEAM_CACHE_DICT = {}
def cache_team_data(baseurl):
    unique_ident = baseurl
    if unique_ident in TEAM_CACHE_DICT:
        return TEAM_CACHE_DICT[unique_ident]
    else:
        response = requests.get(baseurl)
        TEAM_CACHE_DICT[unique_ident] = json.loads(response.text)
        dumped_json_cache = json.dumps(TEAM_CACHE_DICT)
        fw = open(TEAMCACHE, 'w')
        fw.write(dumped_json_cache)
        fw.close()
        return TEAM_CACHE_DICT[unique_ident]

def get_team_data():
    all_team_data = cache_team_data('https://api.sportradar.us/nfl-ot2/league/hierarchy.json?api_key={}'.format(API_KEY))
    team_info_list = []
    for division in all_team_data['conferences'][0]['divisions']:
        team_division = division['name']
        for team in division['teams']:
            team_name = team['name']
            team_id = team['alias']
            team_location = team['market']
            stadium_name = team['venue']['name']
            team_tup = (team_name, team_id, team_location, stadium_name, team_division)
            team_info_list.append(team_tup)
    for division in all_team_data['conferences'][1]['divisions']:
        team_division = division['name']
        for team in division['teams']:
            team_name = team['name']
            team_id = team['alias']
            team_location = team['market']
            stadium_name = team['venue']['name']
            team_tup = (team_name, team_id, team_location, stadium_name, team_division)
            team_info_list.append(team_tup)
    return team_info_list

def populate_Teams(list_of_tuples):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    for team in list_of_tuples:
        team_name = team[0]
        team_id = team[1]
        team_location = team[2]
        stadium_name = team[3]
        team_division = team[4]
        insertion = (None, team_name, team_id, team_location, stadium_name, team_division)
        statement = '''
            INSERT INTO 'Teams'
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        cur.execute(statement, insertion)
        conn.commit()
    conn.close()












#https://api.sportradar.us/nfl-{access_level}{version}/league/hierarchy.{format}?api_key={your_api_key}

#https://api.sportradar.us/nfl-ot2/league/hierarchy.json?api_key=q5zcej3vdue2yamtbu73zf4n













#Get NFL Team data and make a cache from https://developer.sportradar.com/files/indexFootball.html?python#football












#Make a function that creates and adds data FROM THE CACHE to the database


def interactive_prompt():
    response = ''
    playerinfo_response_list = []
    seasonalstats_response_list = []
    while response != 'exit':
        response = input('Enter a command: ')
        if response == 'exit':
            print('Goodbye')
            break
        else:
            init_db()
            populate_Teams(get_team_data())
            while response != 'done':
                playerinfo_response_list += get_QB_data(response)
                seasonalstats_response_list += get_season_data(response)
                response = input('Enter a command: ')



            populate_PlayerInfo(playerinfo_response_list)
            populate_SeasonalStats(seasonalstats_response_list)
            print(name_id)






























if __name__=="__main__":
    interactive_prompt()
