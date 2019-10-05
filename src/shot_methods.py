import csv
from sklearn.linear_model import LogisticRegression
import copy
import sys
import math
import pymysql
from network import fieldLimits
import pickle
import numpy

free_kick = set([5, 23, 24, 30, 43])
set_piece = set([2, 3, 4, 20, 35, 36, 37, 48, 50, 51, 53, 23, 24, 30, 43])
successfullPass = [2,3,4,5,6,8,9,10,15,16,17,19,21,25,28,35,36,37,38,46,48,49,50,53,54,55]

def createFeature(attackType, distGoal, definSight, distDef, backline, midLine, space, speed):
	newFeature = []
	if (attackType == "Open Play"):
		newFeature.extend([1, 0, 0, 0, 0, 0])
	elif (attackType == "Counter Attack"):
		newFeature.extend([0, 1, 0, 0, 0, 0])
	elif (attackType == "Penalty"):
		newFeature.extend([0, 0, 1, 0, 0, 0])
	elif (attackType == "Corner"):
		newFeature.extend([0, 0, 0, 1, 0, 0])
	elif (attackType == "Free Kick"):
		newFeature.extend([0, 0, 0, 0, 1, 0])
	elif (attackType == "Set Play"):
		newFeature.extend([0, 0, 0, 0, 0, 1])
	else:
		print("Bug in code, currently in function createFeature, check variable attackType: " + attackType)
		sys.exit(0)

	newFeature.append(distGoal)
	newFeature.append(definSight)
	newFeature.extend(sorted(distDef, reverse=True))
	while (len(newFeature) < 18):
		newFeature.append(-10)
	newFeature.append(backline)
	newFeature.append(midLine)
	newFeature.append(space)
	newFeature.append(speed)
	return newFeature

def defenderProx(listOfDefenders, lineUp, lineDown, shotX, shotY):
	count = 0
	distList = []
	for defender in listOfDefenders:
		if lieInSight(lineUp, lineDown, defender[0], defender[1]):
			count = count + 1
			distList.append(myEuclidean(shotX, shotY, defender[0], defender[1]))
		else:
			distList.append(-10)

	return (count, distList)

def lieInSight(lineUp, lineDown, x, y):
	if ((y - lineUp[0]*x - lineUp[1] <= 0) and (y - lineDown[0]*x - lineDown[1] >= 0)):
		return True
	return False

def findSpace(lastEvents, listOfDefenders, thisEventId, cur):
	# print test
	# sys.exit()
	# lastEvents = test
	# lastEvents = [x[0] for x in test]
	lastEvents.reverse()
	thisEventId = thisEventId + 1
	counter = -1
	for x in lastEvents:
		counter = counter + 1
		thisEventId = thisEventId - 1
		if x == 2 and ((counter+1 == len(lastEvents)) or (lastEvents[counter + 1] in successfullPass)):
			cur.execute("SELECT x1,y1 FROM events WHERE event_id = %s OR event_id = %s", (thisEventId, thisEventId + 1))
			player1Pos = cur.fetchone()
			player2Pos = cur.fetchone()
			listDistances = [];
			for defender in listOfDefenders:
				listDistances.append(myEuclidean(player1Pos[0],player1Pos[1],defender[0],defender[1]) + \
				myEuclidean(player2Pos[0],player2Pos[1],defender[0],defender[1]))

			distmax = 0;
			count = 0;
			indexMax = 0;
			for distances in listDistances:
				if distances > distmax:
					indexMax = count;
					distmax = distances
				count = count + 1

			distmax1 = 0;
			count = 0;
			indexMax1 = 0;
			for distances in listDistances:
				if distances > distmax1 and distances!=distmax:
					indexMax1 = count;
					distmax1 = distances
				count = count + 1			

			return myEuclidean(listOfDefenders[indexMax][0],listOfDefenders[indexMax][1],listOfDefenders[indexMax1][0],\
			listOfDefenders[indexMax1][1])
	return -10

def myEuclidean(x1,y1,x2,y2):
	return math.sqrt((x2-x1)**2 + (y2-y1)**2)

def getLine(playerX, playerY, goalX, goalY):
	m = (playerY - goalY)/(playerX - goalX)
	c = playerY - m*playerX;
	return (m,c)

def game_context(new_test,distance):
	# new_test = [x[0] for x in test]	
	if new_test[9] == 29:
		return "Penalty"
	else:
		if 12 in new_test:
			check = new_test[new_test.index(12) + 1 :]
			if 17 not in check and 10 not in check and 21 not in check:
				return "Corner"
		if 14 in new_test:
			afterKickEvents = set(new_test[new_test.index(14) + 1 :])
			if afterKickEvents.issubset(free_kick):
				return "Free Kick"
			elif afterKickEvents.issubset(set_piece):
				return "Set Play"
			else:
				return "Open Play"
		else :
			if distance > 0.25:
				return "Counter Attack"
			else:
				return "Open Play"

def roundDown(x):
	return int(math.floor(x / 100.0)) * 100

def createFeatureList(cur):
	features = []
	output = []

	cur.execute("SELECT MAX(y1) FROM events WHERE event_type_id = 21")
	maxGoalY = cur.fetchone()[0]
	cur.execute("SELECT MIN(y1) FROM events WHERE event_type_id = 21")
	minGoalY = cur.fetchone()[0]

	cur.execute("SELECT match_id FROM matches")
	row = cur.fetchall()
	matchList = [y[0] for y in row]

	f = open('features.csv','w')
	csv_file = csv.writer(f)

	for match in matchList:

		xMin, xMax, yMin, yMax = fieldLimits(match, cur)

		cur.execute("SELECT event_id FROM events WHERE (event_type_id = 10 OR event_type_id = 17) and match_id = %s", (match))

		if (cur.rowcount == 0):
			continue

		rows = cur.fetchall()
		shot_time = [x[0] for x in rows]
		# shot_timess = shot_time[15:]

		for x in shot_time:

			cur.execute("SELECT event_type_id, match_id  FROM events WHERE event_id < %s AND event_id >= %s ORDER BY event_id", (x, x-10))
			lastTen = cur.fetchall()
			# print "lastTen: " + str(lastTen)
			lastTen = [y[0] for y in lastTen if y[1] == match]
			# print "lastTen: " + str(lastTen)
			# sys.exit(0)

			cur.execute("SELECT match_time, player1_ps_id, match_half,player1_team_id FROM events WHERE event_id = %s", (x))
			row = cur.fetchone()
			time = roundDown(row[0])

			cur.execute("SELECT x,y FROM tracking_data WHERE match_id = %s AND player_squad_id = %s AND match_time = %s AND \
			match_half = %s", (match, row[1], time, row[2]))
			final_pos = cur.fetchone()

			cur.execute("SELECT x,y FROM tracking_data WHERE match_id = %s AND player_squad_id = %s AND match_time = %s AND \
			match_half = %s", (match, row[1], max(time - 10000,0), row[2]))
			initial_pos = cur.fetchone()

			distance = abs(final_pos[0] - initial_pos[0]) * 1.0/(xMax - xMin)
			attackType = game_context(lastTen,distance)

			if final_pos[0] > 0:
				playerDistanceFromGoal = myEuclidean(final_pos[0],final_pos[1],xMax,0)
				lineUp = getLine(final_pos[0], final_pos[1], xMax, maxGoalY)
				lineDown = getLine(final_pos[0], final_pos[1], xMax, minGoalY)
			else:
				playerDistanceFromGoal = myEuclidean(final_pos[0],final_pos[1],xMin,0)
				lineUp = getLine(final_pos[0], final_pos[1], xMin, maxGoalY)
				lineDown = getLine(final_pos[0], final_pos[1], xMin, minGoalY)

			cur.execute("SELECT x,y FROM tracking_data WHERE match_id = %s AND team_id != %s AND \
				match_time = %s AND match_half = %s AND player_squad_id NOT IN ( \
				SELECT player_squad_id FROM player_squads WHERE player_position_id = 9)", (match, row[3], time, row[2]))

			listOfDefenders = cur.fetchall()
			definSight, distList = defenderProx(listOfDefenders, lineUp, lineDown, final_pos[0], final_pos[1])

			cur.execute("SELECT x FROM `tracking_data` WHERE match_id = %s AND team_id != %s AND match_time = %s AND \
			match_half = %s AND player_squad_id IN (SELECT player_squad_id FROM player_squads WHERE player_position_id = 1 \
			OR	player_position_id=2 OR player_position_id=5 OR player_position_id=11 OR player_position_id=21 OR \
			player_position_id=22 OR player_position_id=20)",(match,row[3],time,row[2]))

			defXPos = cur.fetchall()
			defXPos = [y[0] for y in defXPos]
			backline = (max(defXPos) - min(defXPos))

			cur.execute("SELECT x FROM `tracking_data` WHERE match_id = %s AND team_id != %s AND match_time = %s AND \
			match_half = %s AND player_squad_id IN (SELECT player_squad_id FROM player_squads WHERE player_position_id = 3 \
			OR	player_position_id=6 OR player_position_id=7 OR player_position_id=7 OR player_position_id=10 OR \
			player_position_id=15 OR player_position_id=16 OR player_position_id=17)",(match,row[3],time,row[2]))

			midXPos = cur.fetchall()
			midXPos = [y[0] for y in midXPos]
			if final_pos[0] > 0:
				midLine = min(defXPos) - max(midXPos)
			else:
				midLine = min(midXPos) - max(defXPos)
			space = -10
			if attackType == "Open Play" or attackType == "Counter Attack":
				space = findSpace(lastTen, listOfDefenders, x, cur)

			cur.execute("SELECT AVG(x) FROM tracking_data WHERE match_id = %s AND team_id = %s AND match_time = %s AND \
			match_half = %s", (match, row[3], time, row[2]))
			team1PosXnew = cur.fetchone()[0]

			cur.execute("SELECT AVG(x) FROM tracking_data WHERE match_id = %s AND team_id = %s AND match_time = %s AND \
			match_half = %s", (match, row[3], max(time - 10000,0), row[2]))
			team1PosXold = cur.fetchone()[0]

			attackSpeed = abs(team1PosXold - team1PosXnew)/((time - max(time - 10000,0))/1000.0)

			cur.execute("SELECT AVG(x) FROM tracking_data WHERE match_id = %s AND team_id != %s AND match_time = %s AND \
			match_half = %s", (match, row[3], time, row[2]))


			team2PosXnew = cur.fetchone()[0]
			cur.execute("SELECT AVG(x) FROM tracking_data WHERE match_id = %s AND team_id != %s AND match_time = %s AND \
			match_half = %s", (match, row[3], max(time - 10000,0), row[2]))

			team2PosXold = cur.fetchone()[0]
			defendSpeed = abs(team2PosXold - team2PosXnew)/((time - max(time - 10000,0))/1000)
			relativeSpeed = attackSpeed - defendSpeed

			cur.execute("SELECT player_id FROM player_squads WHERE player_squad_id = %s",(row[1]))
			playerID = cur.fetchone()[0]

			features.append(createFeature(attackType, playerDistanceFromGoal, definSight, distList, backline,\
			midLine, space, relativeSpeed))

			# print("Feature: " + str(features[-1]))

			cur.execute("SELECT event_type_id FROM events WHERE event_id > %s AND event_id < %s", (x, x+3))
			testGoal = cur.fetchall()

			testGoal = [y[0] for y in testGoal]
			if 21 in testGoal:
				output.append(1)
				csv_file.writerow((features[-1], playerID, match, row[3], 1))
			else:
				output.append(0)
				csv_file.writerow((features[-1], playerID, match, row[3], 0))

	f.close()

def createRegressionModel():

	print("Training started")
	f = open('features.csv','r')
	csv_file = csv.reader(f)
	features = []
	output = []
	for row in csv_file:
		temp = row[0][1:-1].split(',')
		if (len(temp) != 22):
			continue
		features.append([float(s) for s in temp])
		output.append(int(row[4]))

	f.close()

	logistic = LogisticRegression()
	logistic.fit(features,output)
	coef = logistic.coef_
	f = open('logistic_model.txt', 'wb')
	pickle.dump(logistic, f)
	f.close()

def getPlayerEGValue(playerID, matches_teams):
	print("Player Evaluation started....")
	print("Player ID: " + str(playerID))

	logistic = pickle.load(open('logistic_model.txt','rb'))
	
	g = open('egv.txt','w')
	

	teams = {}
	for match_team in matches_teams:
		if match_team[1] in teams:
			teams[match_team[1]].append(match_team[0])
		else:
			teams[match_team[1]] = [match_team[0]]

	print("Teams: " + str(teams))
	# sys.exit(0)
	for team in teams:
		features = []
		f = open('features.csv','r')
		csv_file = csv.reader(f)
		for row in csv_file:
			temp = row[0][1:-1].split(',')

			if (len(temp) != 22 or int(row[1])!= playerID or int(row[3])!= team):
				continue
			features.append([float(s) for s in temp])

		if (len(features) == 0):
			continue
		predicted = logistic.predict_proba(features)
		egv1 = sum([x[1] for x in predicted]);
		egv2 = egv1/len(features)
		g.write(str((playerID, team, egv2, egv1)))
		f.close()

	
	g.close()
