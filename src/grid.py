import sys
import math
import pymysql
import matplotlib.pyplot as plt
import csv
from network import fieldLimits

gridLength = 100
gridWidth = 75

def makeBackgroundGrid(cur,cur2):

	cur.execute("SELECT x1,y1,event_type_id, match_id, x2 FROM events WHERE \
		(event_type_id = 10 OR event_type_id = 17 OR event_type_id = 21)")

	shots = [ [ 0 for i in range(gridWidth) ] for j in range(gridLength) ]
	goals = [ [ 0 for i in range(gridWidth) ] for j in range(gridLength) ]
	raw_rate = [ [ 0 for i in range(gridWidth) ] for j in range(gridLength) ]
	prior_mean = [ [ 0 for i in range(gridWidth) ] for j in range(gridLength) ]
	variance = [ [ 0 for i in range(gridWidth) ] for j in range(gridLength) ]
	weights = [ [ 0 for i in range(gridWidth) ] for j in range(gridLength) ]
	effectiveness = [ [ 0 for i in range(gridWidth) ] for j in range(gridLength) ]

	prevX = 0
	prevY = 0
	gridX = 0
	gridY = 0
	row = 0

	for x in range(1,cur.rowcount):
		row = cur.fetchone()
		xMin, xMax, yMin, yMax = fieldLimits(row[3], cur2)

		# cur2.execute("SELECT x FROM `tracking_data` WHERE match_id = %s AND team_id = %s AND match_time = 1000 \
		# 	AND match_half = 1 AND player_squad_id IN (SELECT player_squad_id FROM player_squads WHERE \
		# 	player_position_id = 9)", (row[4],row[5]))

		# if (cur2.rowcount == 0):
		# 	continue

		# goalLocation = cur2.fetchone()[0]

		if (row[4] < 0):
			passLocationX = -abs(xMax/xMin)
			passLocationY = -abs(yMax/yMin)
		else:
			passLocationX = 1
			passLocationY = 1



		if (row[0] < -10000 or row[1] < -10000):
			continue

		gridX = int(math.floor((((row[0]*passLocationX) - xMin)*gridLength) / (xMax - xMin)))
		gridY = int(math.floor((((row[1]*passLocationY) - yMin)*gridWidth) / (yMax - yMin)))

		if (gridX <= 45 and gridX >= 0):
			
			print ("Type: " + str(row[2]))
			print ("xMin: " + str(xMin))
			print ("xMax: " + str(xMax))
			print ("yMin: " + str(yMin))
			print ("yMax: " + str(yMax))
			print('Shot Position X: ' + str(row[0]))
			print('Shot Position Y: ' + str(row[1]))
			print ("gridX: " + str(gridX))
			print ("gridY: " + str(gridY))
			print ("prevX: " + str(prevX))
			print ("prevY: " + str(prevY))
			print ("Goal Location: " + str(row[4]))
			print ("Match Half: " + str(row[3]))
			print ("Pass Location: " + str(passLocationX))
			sys.exit()

		if gridX == gridLength:
			gridX -= 1

		if gridY == gridWidth:
			gridY -= 1

		# print "gridX: " + str(gridX)
		# print "gridY: " + str(gridY)
		# print "X: " + str(row[0])
		# print "Y: " + str(row[1])
		# print "match_id: " + str(row[3])
		# print "team_id: " + str(row[5])
		# print "Event type: " + str(row[2])

		# if (gridX  == 8):
		# 	sys.exit(0)
		try:
			if (row[2] == 10 or row[2] == 17):
				shots[gridX][gridY] = shots[gridX][gridY] + 1
				prevX = gridX
				prevY = gridY
			else:
				goals[prevX][prevY] = goals[prevX][prevY] + 1
		except IndexError as E:
			print('Ignoring index error')
			continue
			# print('Type: ' + str(row[2]))
			# print('Shot Position X: ' + str(row[0]))
			# print('Shot Position Y: ' + str(row[1]))
			# print('Pass Location X: ' + str(passLocationX))
			# print('Pass Location Y: ' + str(passLocationY))
			# print('Grid X: ' + str(gridX))
			# print('Grid Y: ' + str(gridY))
			# print('Max X: ' + str(xMax))
			# print('Min X: ' + str(xMin))
			# print('Max Y: ' + str(yMax))
			# print('Min Y: ' + str(yMin))
			# print('Prev X: ' + str(prevX))
			# print('Prev Y: ' + str(prevY))
			# print('Error: ' + str(E))
			# print('Error in grid File')
			# sys.exit()


	f = open('Shots.csv','w')
	csv_file = csv.writer(f)
	csv_file.writerows(shots)
	f.close()

	f = open('Goals.csv','w')
	csv_file = csv.writer(f)
	csv_file.writerows(goals)
	f.close()

	for x in range(0,gridLength):
		for y in range(0,gridWidth):
			try:
				raw_rate[x][y] = (goals[x][y])/float(shots[x][y])
			except ZeroDivisionError:
				raw_rate[x][y] = 0
			tempShot = 0
			tempGoal = 0
			for a in range(-1,1):
				for b in range(-1,1):
					try:
						tempShot = tempShot + shots[x+a][y+b]
						tempGoal = tempGoal + goals[x+a][y+b]
					except IndexError:
						tempShot = tempShot
						tempGoal = tempGoal
			try:
				prior_mean[x][y] = tempGoal/float(tempShot)
			except ZeroDivisionError:
				prior_mean[x][y] = 0


	for x in range(0,gridLength):
		for y in range(0,gridWidth):
			tempVar = 0
			tempTotal = 0
			for a in range(-1,1):
				for b in range(-1,1):
					try:
						tempVar = tempVar + (shots[x+a][y+b])*((raw_rate[x+a][y+b] - prior_mean[x+a][y+b])**2)
						tempTotal = tempTotal + shots[x+a][y+b]
					except IndexError:
						tempVar = tempVar
			try:
				variance[x][y] = tempVar / float(tempTotal) - (prior_mean[x][y] / (tempTotal/9.0))
				if (variance[x][y] < 0):
					variance[x][y] = 0
			except ZeroDivisionError:
				variance[x][y] = 0

			try:
				weights[x][y] = variance[x][y] / (variance[x][y] + (prior_mean[x][y]/float(shots[x][y])))
			except ZeroDivisionError:
				weights[x][y] = 0		
			
			effectiveness[x][y] = weights[x][y]*raw_rate[x][y] + (1- weights[x][y])*prior_mean[x][y]


	f = open('rawRate.csv','w')
	csv_file = csv.writer(f)
	csv_file.writerows(raw_rate)
	f.close()

	f = open('weights.csv','w')
	csv_file = csv.writer(f)
	csv_file.writerows(weights)
	f.close()

	f = open('effectiveness.csv','w')
	csv_file = csv.writer(f)
	csv_file.writerows(effectiveness)
	f.close()

	f = open('prior_mean.csv','w')
	csv_file = csv.writer(f)
	csv_file.writerows(prior_mean)
	f.close()


def shootingEffectiveness(playerID, matches_teams, cur):
	f = open('effectiveness.csv', 'r')
	effectiveness = []
	csv_file = csv.reader(f)
	for row in csv_file:
		effectiveness.append([float(i) for i in row ])

	f.close()
	# teams = set([y[1] for y in matches_teams])
	# matches = 
	teams = {}
	for match_team in matches_teams:
		if match_team[1] in teams:
			teams[match_team[1]].append(match_team[0])
		else:
			teams[match_team[1]] = [match_team[0]]
	# myDict = dict((y, x) for x, y in matches_teams)
	# print myDict
	# print teams
	# sys.exit(0)

	f = open('playerGrid.txt','w')
	for team in teams:

		shots = [ [ 0 for i in range(gridWidth) ] for j in range(gridLength) ]
		goals = [ [ 0 for i in range(gridWidth) ] for j in range(gridLength) ]
		expectedLocalPoints = [ [ 0.0 for i in range(gridWidth) ] for j in range(gridLength) ]
		localGoalsPerShot = [ [ 0.0 for i in range(gridWidth) ] for j in range(gridLength) ]
		localPointDifference = [ [ 0.0 for i in range(gridWidth) ] for j in range(gridLength) ]
		lsse = [ [ 0.0 for i in range(gridWidth) ] for j in range(gridLength) ]

		totalShots = 0
		totalGoals = 0

		for match in teams[team]:

			xMin, xMax, yMin, yMax = fieldLimits(match, cur)

			cur.execute("SELECT events.x1, events.y1, events.event_type_id, events.x2 FROM events INNER JOIN player_squads \
				ON events.player1_ps_id = player_squads.player_squad_id WHERE match_id = %s AND (event_type_id = 10 \
				OR event_type_id = 17 OR event_type_id = 21) AND player_id = %s AND player1_team_id = %s", (match, playerID, team))

			if (cur.rowcount == 0):
				continue

			# print "Row: " + str(cur.fetchone())
			# print "Team: " +  str(team)
			# print "Match: " + str(match)
			# sys.exit(0)
			# print 

			prevX = 0
			prevY = 0
			gridX = 0
			gridY = 0
			row = 0

			for x in range(1,cur.rowcount):
				row = cur.fetchone()
				# print "Row: " + str(row)

				# print "Row2: " + str(row)
				if (row[3] < 0):
					passLocationX = -abs(xMax/xMin)
					passLocationY = -abs(yMax/yMin)
				else:
					passLocationX = 1
					passLocationY = 1

				gridX = int(math.floor((((row[0]*passLocationX) - xMin)*gridLength) / (xMax - xMin)))
				gridY = int(math.floor((((row[1]*passLocationY) - yMin)*gridWidth) / (yMax - yMin)))

				try:
					if (row[2] == 10 or row[2] == 17):
						shots[gridX][gridY] = shots[gridX][gridY] + 1
						totalShots = totalShots + 1
						prevX = gridX
						prevY = gridY
					else:
						goals[prevX][prevY] = goals[prevX][prevY] + 1
						totalGoals = totalGoals + 1
				except IndexError as E:
					print('Ignoring index error')
					continue

		if (totalShots == 0):
			continue
		
		# expectedLocalPoints = [a*b for a,b in zip(effectiveness,shots)]

		wsse = 0.0
		wssk = 0.0
		for i in range(gridLength):
			for j in range(gridWidth):
				expectedLocalPoints[i][j] = effectiveness[i][j] * shots[i][j]
				if (shots[i][j] != 0):
					localGoalsPerShot[i][j] = float(goals[i][j])/float(shots[i][j])
					localPointDifference[i][j] = (goals[i][j] - expectedLocalPoints[i][j])/shots[i][j]
				lsse[i][j] = localGoalsPerShot[i][j] - effectiveness[i][j]
				# if (lsse[i][j] != 0):
				# 	print 'lsse: ' + str(lsse[i][j])
				wsse = wsse + shots[i][j] * lsse[i][j]
				wssk = wssk + shots[i][j] * lsse[i][j] * lsse[i][j]

		wssk = wssk/(float(totalShots)/(gridLength*gridWidth))
		wsse = wsse/float(totalShots)
		expectedGoalsPerShot = (sum(map(sum, expectedLocalPoints)))/float(totalShots)
		goalsPerShot = totalGoals/float(totalShots)
		spatialShootingEffectiveness = goalsPerShot - expectedGoalsPerShot
		pola = spatialShootingEffectiveness * totalShots

		# print 'wsse: ' + str(wsse)
		# print 'wssk: ' + str(wssk)

		f.write(str((team, playerID, goalsPerShot, spatialShootingEffectiveness, pola, wsse, wssk)))

		g = open('elp_' + str(team) + '_' + str(playerID) + '.csv','w')
		csv_file = csv.writer(g)
		csv_file.writerows(expectedLocalPoints)
		g.close()

		g = open('lgps_' + str(team) + '_' + str(playerID) + '.csv','w')
		csv_file = csv.writer(g)
		csv_file.writerows(localGoalsPerShot)
		g.close()

		g = open('lpd_' + str(team) + '_' + str(playerID) + '.csv','w')
		csv_file = csv.writer(g)
		csv_file.writerows(localPointDifference)
		g.close()

		g = open('lsse_' + str(team) + '_' + str(playerID) + '.csv','w')
		csv_file = csv.writer(g)
		csv_file.writerows(lsse)
		g.close()


