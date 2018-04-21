import requests
import json
import sqlite3
from bs4 import BeautifulSoup
import plotly.plotly as py
import plotly.graph_objs as go

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
            'YearBorn' INTEGER,
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
            'Year' INTEGER,
            'Age' INTEGER,
            'Wins' INTEGER,
            'Losses' INTEGER,
            'CompletionPercent' REAL,
            'PassYards' INTEGER,
            'Touchdowns' INTEGER,
            'Interceptions' INTEGER,
            'Rating' REAL
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
    html = 'https://www.pro-football-reference.com/players/qbindex.htm'
    page_html = cache_QB_data(html)
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
        player_info = qb_soup.find(itemtype='https://schema.org/Person')
        #Get name
        player_name = player_info.find(itemprop='name').string
        ptags = player_info.find_all('p')
        for p in ptags:
            if 'Born' in p.text:
                year_born = p.find('span')['data-birth'][0:4]
        ptags = player_info.find_all('p')
        for p in ptags:
            if 'College' in p.text:
                college = p.find('a').text
        passing_info = qb_soup.find(id='passing')
        passing_table = passing_info.find('tbody')
        table_elements = passing_table.find_all('tr')
        player_teams = []
        return_list = []
        for tr in table_elements:
            td_list = tr.find_all('td', attrs={'data-stat': 'team'})
            for td in td_list:
                if td.string not in player_teams:
                    player_teams.append(td.string)
        for team in player_teams:
            return_list.append((player_name, int(year_born), college, team))
        return return_list
    else:
        return 'not a QB name'


def populate_PlayerInfo(list_of_tuples):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    global name_id
    global counter
    for player in list_of_tuples:
        player_name = player[0].strip()
        if player_name not in name_id.keys():
            name_id[player_name] = counter
            counter += 1
        year_born = player[1]
        college = player[2]
        team = player[3]
        insertion = (None, player_name, name_id[player_name], year_born,
                        college, team)
        statement = '''
            INSERT INTO 'PlayerInfo'
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        cur.execute(statement, insertion)
        conn.commit()
    conn.close()


def get_season_data(name):
    html = 'https://www.pro-football-reference.com/players/qbindex.htm'
    page_html = cache_QB_data(html)
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
            try:
                record_parts = record.split('-')
                wins = int(record_parts[0])
                losses = int(record_parts[1])
            except:
                wins = 'n/a'
                losses = 'n/a'
            comp_percent = row.find(attrs={'data-stat': 'pass_cmp_perc'}).string
            try:
                comp_percent = float(comp_percent)
            except:
                comp_percent = 'n/a'
            pass_yards = row.find(attrs={'data-stat': 'pass_yds'}).string
            try:
                pass_yards = int(pass_yards)
            except:
                pass_yards = 'n/a'
            passing_tds = row.find(attrs={'data-stat': 'pass_td'}).string
            try:
                passing_tds = int(passing_tds)
            except:
                passing_tds = 'n/a'
            interceptions = row.find(attrs={'data-stat': 'pass_int'}).string
            try:
                interceptions = int(interceptions)
            except:
                interceptions = 'n/a'
            try:
                qbr = row.find(attrs={'data-stat': 'qbr'}).string
                qbr = float(qbr)
            except:
                qbr = 'n/a'
            info = (name, int(year), int(age), team, wins, losses, comp_percent,
                    pass_yards, passing_tds, interceptions, qbr)
            info_list.append(info)
        return info_list
    else:
        return 'not a name'


def populate_SeasonalStats(list_of_tuples):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    global name_id
    global counter
    for season in list_of_tuples:
        player_name = season[0].strip()
        year = season[1]
        player_age = season[2]
        team = season[3]#
        wins = season[4]
        losses = season[5]
        comp_percent = season[6]
        pass_yards = season[7]
        passing_tds = season[8]
        interceptions = season[9]
        playeridnum = name_id[player_name]
        qbr = season[10]
        insertion = (None, player_name, playeridnum, team, year, player_age,
                        wins, losses, comp_percent, pass_yards, passing_tds,
                        interceptions, qbr)
        statement = '''
            INSERT INTO 'SeasonalStats'
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    html = 'https://api.sportradar.us/nfl-ot2/league/hierarchy.json?api_key={}'.format(API_KEY)
    all_team_data = cache_team_data(html)
    team_info_list = []
    for division in all_team_data['conferences'][0]['divisions']:
        team_division = division['name']
        for team in division['teams']:
            team_name = team['name']
            team_id = team['alias']
            team_location = team['market']
            stadium_name = team['venue']['name']
            team_tup = (team_name, team_id, team_location, stadium_name,
                        team_division)
            team_info_list.append(team_tup)
    for division in all_team_data['conferences'][1]['divisions']:
        team_division = division['name']
        for team in division['teams']:
            team_name = team['name']
            team_id = team['alias']
            team_location = team['market']
            stadium_name = team['venue']['name']
            team_tup = (team_name, team_id, team_location, stadium_name,
                        team_division)
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
        insertion = (None, team_name, team_id, team_location, stadium_name,
                        team_division)
        statement = '''
            INSERT INTO 'Teams'
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        cur.execute(statement, insertion)
        conn.commit()
    conn.close()


def get_all_QB_names():
    html = 'https://www.pro-football-reference.com/players/qbindex.htm'
    page_html = cache_QB_data(html)
    page_soup = BeautifulSoup(page_html, 'html.parser')
    data = page_soup.find(id='div_players')
    moredata = data.find('tbody')
    qb_data = moredata.find_all('tr')
    all_QB_names = []
    for qb in qb_data:
        qb_name = qb.find('a').string
        all_QB_names.append(qb_name)
    return all_QB_names


def process_command(command):
    query = command.split(' ')
    main_commands = ['list', 'compare']
    control_dict = {'main': '', 'qb1': '', 'qb2': '', 'season': '', 'stat': ''}
    stat_options = ['team', 'age', 'record', 'completions', 'passyards',
                    'touchdowns', 'interceptions', 'rating', 'stats']
    all_QB_names = get_all_QB_names()
    if query[0] not in main_commands:
        return 'Invalid command'
        print('gggggg')
    elif query[0] == 'list':
        control_dict['main'] = query[0]
        try:
            firstname = query[1]
            lastname = query[2]
        except:
            return 'Invalid command'
        player_name = firstname + ' ' + lastname
        if player_name in all_QB_names:
            control_dict['qb1'] = player_name
        else:
            return 'Invalid command'
        try:
            if query[3] in stat_options:
                control_dict['stat'] = query[3]
            else:
                return 'Invalid command'
        except:
            return 'Invalid command'
    elif query[0] == 'compare':
        control_dict['main'] = query[0]
        try:
            firstname1 = query[1]
            lastname1 = query[2]
        except:
            return 'Invalid command'
        qb1name = firstname1 + ' ' + lastname1
        if qb1name in all_QB_names:
            control_dict['qb2'] = qb1name
        else:
            return 'Invalid command'
        try:
            firstname2 = query[4]
            lastname2 = query[5]
        except:
            return 'Invalid command'
        qb2name = firstname2 + ' ' + lastname2
        if qb2name in all_QB_names:
            control_dict['qb2'] = qb2name
        else:
            return 'Invalid command'
        qb2name = firstname2 + ' ' + lastname2
        if qb1name and qb2name in all_QB_names:
            control_dict['qb1'] = qb1name
            control_dict['qb2'] = qb2name
        else:
            return 'Invalid command'
        try:
            if query[6] in stat_options:
                control_dict['stat'] = query[6]
            else:
                return 'Invalid command'
        except:
            return 'Invalid command'
    else:
        return 'Invalid command'
    return control_dict


def list_info(control_dict):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    player_name = control_dict['qb1']
    stat_spec = control_dict['stat']
    if control_dict['main'] == 'list':
        if stat_spec == 'stats':
            statement = '''
                SELECT Name, Team, Year, Age, Wins, Losses, CompletionPercent,
                PassYards, Touchdowns, Interceptions, Rating
                FROM SeasonalStats
                WHERE Name='{}'
                ORDER BY Year ASC
            '''.format(player_name)
        else:
            statement = '''
                SELECT Name, Year, {}
                FROM SeasonalStats
                WHERE Name='{}'
                ORDER BY Year ASC
            '''.format(stat_spec, player_name)
        cur.execute(statement)
        info_list = []
        for row in cur:
            info_list.append(row)
        return info_list
    if control_dict['main'] == 'compare':
        player_name2 = control_dict['qb2']
        if stat_spec == 'stats':
            statement = '''
                SELECT Name, Team, Year, Age, Wins, Losses, CompletionPercent,
                PassYards, Touchdowns, Interceptions, Rating
                FROM SeasonalStats
                WHERE Name='{}'
                ORDER BY Year ASC
            '''.format(player_name)
            cur.execute(statement)
            info_list1 = []
            for row in cur:
                info_list1.append(row)

            statement = '''
                SELECT Name, Team, Year, Age, Wins, Losses, CompletionPercent,
                PassYards, Touchdowns, Interceptions, Rating
                FROM SeasonalStats
                WHERE Name='{}'
                ORDER BY Year ASC
            '''.format(player_name2)
            cur.execute(statement)
            info_list2 = []
            for row in cur:
                info_list2.append(row)
        else:
            statement = '''
                SELECT Name, Year, {}
                FROM SeasonalStats
                WHERE Name='{}'
                ORDER BY Year ASC
            '''.format(stat_spec, player_name)
            cur.execute(statement)
            info_list1 = []
            for row in cur:
                info_list1.append(row)

            statement = '''
                SELECT Name, Year, {}
                FROM SeasonalStats
                WHERE Name='{}'
                ORDER BY Year ASC
            '''.format(stat_spec, player_name2)
            cur.execute(statement)
            info_list2 = []
            for row in cur:
                info_list2.append(row)

        return info_list1, info_list2




def get_plotly_for_one(list_of_tuples):
    years = []
    stats = []
    for tup in list_of_tuples:
        year = tup[1]
        stat = tup[2]
        years.append(year)
        stats.append(stat)

    trace = go.Bar(
        x = years,
        y = stats
    )
    data = [trace]
    py.plot(data, filename='basic-bar')

def get_plotly_for_two(list_of_tuples):
    years = []
    stats1 = []
    stats2 = []
    for tup in list_of_tuples[0]:
        year = tup[1]
        stat = tup[2]
        years.append(year)
        stats1.append(stat)
    for tup in list_of_tuples[1]:
        year = tup[1]
        stat = tup[2]
        years.append(year)
        stats2.append(stat)
    player1 = go.Bar(
        x = years,
        y = stats1
    )
    player2 = go.Bar(
        x = years,
        y = stats2
    )
    data = [player1, player2]
    layout = go.Layout(
        barmode='group'
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='grouped-bar')


def interactive_prompt():
    response = ''
    playerinfo_response_list = []
    seasonalstats_response_list = []
    player_names = []
    init_db()
    populate_Teams(get_team_data())
    all_QB_names = get_all_QB_names()
    response = input('Enter a command: ')
    if response == 'exit':
        print('Goodbye')
    while response != 'exit':
        if response == 'help':
            f = open('README.txt', 'r')
            helptext = f.read()
            print(helptext)
            response = input('Enter a command: ')
            continue
        control_dict = process_command(response)
        if control_dict == 'Invalid command':
            print('Invalid command, try again or type "help" ')
        else:
            ns = []
            player_name = control_dict['qb1']
            player_name2 = control_dict['qb2']
            if player_name2 != '':
                ns.append(player_name2)
            ns.append(player_name)
            main_command = control_dict['main']
            for p in ns:
                if p not in player_names:
                    if p not in all_QB_names:
                        print("That's not a QB name")
                    else:
                        populate_PlayerInfo(get_QB_data(p))
                        populate_SeasonalStats(get_season_data(p))
                        player_names.append(p)
            if main_command == 'list':
                for row in list_info(control_dict):
                    rowlist = []
                    for word in row:
                        formatted = format(word, '>8')
                        rowlist.append(formatted)
                    txt = ''
                    for item in rowlist:
                        txt += item
                    print(txt)
                if control_dict['stat'] != 'stats':
                    get_plotly_for_one(list_info(control_dict))
            elif main_command == 'compare':
                for bigtup in list_info(control_dict):
                    for row in bigtup:
                        rowlist = []
                        for word in row:
                            if word == row[0]:
                                word = format(word, '<18')
                                rowlist.append(word)
                                continue
                            formatted = format(word, '>8')
                            rowlist.append(formatted)
                        txt = ''
                        for item in rowlist:
                            txt += item
                        print(txt)
                    if control_dict['stat'] != 'stats':
                        get_plotly_for_two(list_info(control_dict))
        response = input('Enter a command: ')


if __name__=="__main__":
    interactive_prompt()
