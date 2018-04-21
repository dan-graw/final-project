import unittest
from finalproj import *


qb_list = ['Tom Brady', 'Mark Sanchez', 'Peyton Manning', 'Brett Favre', 'Eli Manning']
init_db()
populate_Teams(get_team_data())
for p in qb_list:
    populate_PlayerInfo(get_QB_data(p))
    populate_SeasonalStats(get_season_data(p))

class TestDatabase(unittest.TestCase):


    def test_PlayerInfo(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = 'SELECT Name FROM PlayerInfo'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertIn(('Eli Manning',), result_list)
        self.assertEqual(len(result_list), 11)

        sql = '''
            SELECT Team FROM PlayerInfo
            WHERE Team='NYJ'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(len(result_list), 2)
        sql = 'SELECT * FROM PlayerInfo'
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(result_list[0][5], 'NWE')

        conn.close()


    def test_SeasonalInfo(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT Name, NameId FROM SeasonalStats
            WHERE Name='Peyton Manning'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        for res in result_list:
            self.assertEqual(res[1], 3)

        sql = 'SELECT Age FROM SeasonalStats'
        results = cur.execute(sql)
        result_list = results.fetchall()
        for res in result_list:
            self.assertEqual(type(res[0]), int)


    def test_TeamInfo(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT TeamName, Stadium FROM Teams
            WHERE TeamName='Bears'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(result_list[0][1], 'Soldier Field')


    def test_joins(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        sql = '''
            SELECT Name
            FROM PlayerInfo
	          JOIN Teams
	          ON PlayerInfo.Team=Teams.TeamId
            WHERE TeamName='Broncos'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(result_list[0][0], 'Peyton Manning')

        sql = '''
            SELECT PlayerInfo.Name
            FROM PlayerInfo
	          JOIN SeasonalStats
	          ON PlayerInfo.NameID=SeasonalStats.NameId
            WHERE College='Michigan'
        '''
        results = cur.execute(sql)
        result_list = results.fetchall()
        self.assertEqual(result_list[0][0], 'Tom Brady')

class TestSearches(unittest.TestCase):

    def test_list_info(self):
        command = 'list Brett Favre stats'
        result_list = list_info(process_command(command))
        self.assertEqual(result_list[0][3], 22)

        command = 'list Mark Sanchez interceptions'
        result_list = list_info(process_command(command))
        self.assertEqual(result_list[4][2], 11)

    def test_compare_info(self):
        command = 'compare Tom Brady and Peyton Manning stats'
        result_list = list_info(process_command(command))
        self.assertEqual(len(result_list), 2)




unittest.main()
