import sys
import pymysql
from network import playerPassGraph, playerZonalGraph
from grid import makeBackgroundGrid, shootingEffectiveness
from in_game import createCluster, playerPrediction
from shot_methods import createRegressionModel, createFeatureList, getPlayerEGValue

def main(_host, _user, _password, _db):
	print('Python Version: ' + str(sys.version_info[0]) + '.' + str(sys.version_info[1]) + '.' + \
		str(sys.version_info[2]))

	db = pymysql.connect(host = _host, user = _user, passwd = _password, db = _db, port = 3307)
	cur = db.cursor()
	print("1st connection established")

	db2 = pymysql.connect(host = _host, user = _user, passwd = _password, db = _db, port = 3307)
	cur2 = db2.cursor()	
	print("2nd connection established")
		
	# Find players who have played in multiple teams. Returns player_id, number of teams played with
	cur.execute("SELECT player_squads.player_id, COUNT(DISTINCT squads.team_id) FROM squads \
		INNER JOIN player_squads ON player_squads.squad_id = squads.squad_id WHERE (player_position_id = 4 OR \
			player_position_id = 12 OR player_position_id = 13 OR player_position_id = 14 OR player_position_id = 19) \
		GROUP BY player_id HAVING COUNT(DISTINCT squads.team_id) > 1")

	print("Query 1 done")
	multipleTeamplayers = list(cur.fetchall())
	multipleTeamplayers = [y[0] for y in multipleTeamplayers]


	# # Returns player_id, goals scored by a player
	cur.execute("SELECT player_id, COUNT(*) FROM `player_squads` INNER JOIN events ON \
		events.player1_ps_id = player_squads.player_squad_id WHERE event_type_id=21 \
		GROUP BY player_id ORDER BY COUNT(*) DESC")
	print("Query 2 done")
	playerGoals = list(cur.fetchall())

	for x in playerGoals:
		if x[0] in multipleTeamplayers:
			selectedPlayer = x[0]
			break

	print('Selected Player: ' + str(selectedPlayer))

	cur.execute("SELECT match_id, team_id FROM squads WHERE squad_id IN (SELECT squad_id FROM player_squads \
		WHERE player_id = %s)", (selectedPlayer))

	print("Query 3 done")
	matchesByPlayer = list(cur.fetchall())

	print("Matches By Player: " + str(matchesByPlayer))

	print("Going in network file")
	playerPassGraph(selectedPlayer, matchesByPlayer, cur)
	playerZonalGraph(selectedPlayer, matchesByPlayer, cur)

	print("Going in Grid File")
	makeBackgroundGrid(cur,cur2)

	print("Going in shooting effectiveness")
	shootingEffectiveness(selectedPlayer, matchesByPlayer, cur)

	print("Going in movements")
	createCluster(cur, cur2)
	playerPrediction(selectedPlayer, matchesByPlayer,cur, cur2)

	print("Going in shot_methods")
	createFeatureList(cur)
	createRegressionModel()
	getPlayerEGValue(selectedPlayer, matchesByPlayer)

	print("Program Complete")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
