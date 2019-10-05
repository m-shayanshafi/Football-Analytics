from scipy import spatial
import pymysql
import math
import sys
from sklearn.cluster import MiniBatchKMeans
import numpy as np
import pickle
import csv

def myEuclidean(x1,y1,x2,y2):
	return math.sqrt((x2-x1)**2 + (y2-y1)**2)

def CosineDist(vec1, vec2):
	return spatial.distance.cosine(vec1, vec2)

# fixedPlayerId = 23
# fixedMatchId = 1
gotPossession = [3,4] 
lostPossession = [2,7,8,9,10,13,14,17,21,26,29,32,35,36,37,38]

# 	# 	sys.exit()
# 	oneItem = [y[0] for y in PlayerDictionary[key]]
# 	# print oneItem
# 	# sys.exit(0)
# 	labels = kmeans.predict(oneItem)
# 	PlayerFeatureVector[key] = []
# 	for num in range(0,200):
# 		PlayerFeatureVector[key].append(np.count_nonzero(labels == num))

# PlayerCosineDistance = dict.fromkeys(playerIDs)

# for key in PlayerCosineDistance:
# 	PlayerCosineDistance[key] = [float("inf")] * 5
# 	for key2 in PlayerFeatureVector:
# 		cosDistance = CosineDist(PlayerFeatureVector[key], PlayerFeatureVector[key2])
# 		if cosDistance < max(PlayerCosineDistance[key]) and key != key2:
# 			minIndex = PlayerCosineDistance[key].index(max(PlayerCosineDistance[key]))
# 			PlayerCosineDistance[key][minIndex] = cosDistance

# 	PlayerCosineDistance[key] = sum(PlayerCosineDistance[key])
# 	# print PlayerCosineDistance[key]

# listofMatches = list(set([y[1] for y in PlayerDictionary[416]]))


# print listofMatches

def createCluster(cur, cur2):
	cur.execute("SELECT DISTINCT(player_squad_id) FROM player_squads WHERE player_position_id != 9")
	allPlayers = cur.fetchall()
	allPlayers = [y[0] for y in allPlayers]

	cur.execute("SELECT DISTINCT(player1_ps_id) FROM events")
	playerInEvents = cur.fetchall()
	playerInEvents = [y[0] for y in playerInEvents]

	playerIDs = list(set(playerInEvents) & set(allPlayers))
	PlayerDictionary = dict.fromkeys(playerIDs)

	prevMatchID = 0
	prevMatchHalf = 0

	for playerID in playerIDs:

		cur.execute("SELECT event_id,x1,y1,event_type_id, match_time, player1_team_id, match_id, match_half FROM events WHERE player1_ps_id = %s ORDER BY event_id", (playerID))
		# playerEvents = cur.fetchall()
		# teamID = playerEvents[0][5]

		ballGained = 0
		completeList = []
		oneVector = []

		# x1,y1, T, b, s, x2, y2
		for x in range(cur.rowcount):
			event = cur.fetchone()
			matchID = event[6]
			teamID = event[5]
			matchHalf = event[7]
			if (oneVector and (prevMatchID != matchID or prevMatchHalf != matchHalf)):
				oneVector = []
				prevMatchHalf = matchHalf
				prevMatchID = matchID
				continue

			cur2.execute("SELECT home_team_id, away_team_id FROM matches WHERE match_id = %s",(matchID))
			teamSide = cur2.fetchone()
			# print teamSide
			# sys.exit()

			if (teamSide[0] == teamID and matchHalf == 1):
				multiplier = 1
			elif (teamSide[0] == teamID and matchHalf == 2):
				multiplier = -1
			elif (teamSide[1] == teamID and matchHalf == 1):
				multiplier = -1
			elif (teamSide[1] == teamID and matchHalf == 2):
				multiplier = 1

			if (event[3] in gotPossession and not oneVector):

				oneVector.append(event[1] * multiplier)
				oneVector.append(event[2] * multiplier)
				oneVector.append(event[4])
				oneVector.append(1)
			elif (event[3] in lostPossession and not oneVector):
				oneVector.append(event[1] * multiplier)
				oneVector.append(event[2] * multiplier)
				oneVector.append(event[4])
				oneVector.append(0)
			elif (event[3] in gotPossession or event[3] in lostPossession):
				distance = myEuclidean(event[1],event[2],oneVector[0], oneVector[1])
				oneVector.append(distance/(event[4] - oneVector[2]))
				oneVector.append(event[1] * multiplier)
				oneVector.append(event[2] * multiplier)
				completeList.append(oneVector)
				oneVector = []

			prevMatchHalf = matchHalf
			prevMatchID = matchID

		PlayerDictionary[playerID] = completeList

	allEvents = PlayerDictionary.values()
	allEvents = [item for sublist in allEvents for item in sublist]
	# print allEvents
	# sys.exit()
	X = np.array(allEvents)
	kmeans = MiniBatchKMeans(n_clusters=200).fit(X)

	f = open('allPlayerMovements.txt', 'wb')
	pickle.dump(kmeans, f)
	f.close()

def playerPrediction(playerID, matches_teams, cur, cur2):
	kmeans = pickle.load(open('allPlayerMovements.txt','rb'))

	teams = {}
	for match_team in matches_teams:
		if match_team[1] in teams:
			teams[match_team[1]].append(match_team[0])
		else:
			teams[match_team[1]] = [match_team[0]]


	for team in teams:
		cur.execute("SELECT events.event_id,events.x1, events.y1, events.event_type_id, events.match_time, events.match_id,\
		events.match_half FROM events INNER JOIN player_squads ON events.player1_ps_id = player_squads.player_squad_id WHERE \
		player_id = %s AND player1_team_id = %s ORDER BY events.event_id", (playerID, team))

		if (cur.rowcount == 0):
			continue

		ballGained = 0
		completeList = []
		oneVector = []

		# x1,y1, T, b, s, x2, y2
		for x in range(cur.rowcount):
			event = cur.fetchone()
			matchID = event[5]
			# teamID = event[
			matchHalf = event[6]
			if (oneVector and (prevMatchID != matchID or prevMatchHalf != matchHalf)):
				oneVector = []
				prevMatchHalf = matchHalf
				prevMatchID = matchID
				continue

			cur2.execute("SELECT home_team_id, away_team_id FROM matches WHERE match_id = %s",(matchID))
			teamSide = cur2.fetchone()


			if (teamSide[0] == team and matchHalf == 1):
				multiplier = 1
			elif (teamSide[0] == team and matchHalf == 2):
				multiplier = -1
			elif (teamSide[1] == team and matchHalf == 1):
				multiplier = -1
			elif (teamSide[1] == team and matchHalf == 2):
				multiplier = 1

			if (event[3] in gotPossession and not oneVector):
				oneVector.append(event[1] * multiplier)
				oneVector.append(event[2] * multiplier)
				oneVector.append(event[4])
				oneVector.append(1)
			elif (event[3] in lostPossession and not oneVector):
				oneVector.append(event[1] * multiplier)
				oneVector.append(event[2] * multiplier)
				oneVector.append(event[4])
				oneVector.append(0)
			elif (event[3] in gotPossession or event[3] in lostPossession):
				distance = myEuclidean(event[1],event[2],oneVector[0], oneVector[1])
				oneVector.append(distance/(event[4] - oneVector[2]))
				oneVector.append(event[1] * multiplier)
				oneVector.append(event[2] * multiplier)
				completeList.append((oneVector, matchID))
				oneVector = []

			prevMatchHalf = matchHalf
			prevMatchID = matchID

		# print completeList
		g = open('ingame_' + str(team) + '_' + str(playerID) + '.csv','w')
		csv_file = csv.writer(g)
		csv_file.writerows(completeList)
		g.close()
		# sys.exit(0)
		PlayerFeatureVector = {}
		for match in teams[team]:
			# print str([y[0] for y in completeList if y[1] == match])
			# sys.exit(0)
			currentList = [y[0] for y in completeList if y[1] == match]
			if not currentList:
				continue
			labels = kmeans.predict([y[0] for y in completeList if y[1] == match])
			PlayerFeatureVector[match] = []
			for num in range(0,200):
				PlayerFeatureVector[match].append(np.count_nonzero(labels == num))

		consistency = {}
		for match in PlayerFeatureVector:
			count = 0
			consistency[match] = 0
			for match2 in PlayerFeatureVector:
				consistency[match] = consistency[match] + CosineDist(PlayerFeatureVector[match], PlayerFeatureVector[match2])
				count = count + 1

			consistency[match] = consistency[match]/float(count)

		g = open('consistency_' + str(team) + '_' + str(playerID) + '.txt','w')
		g.write(str(consistency))
		g.close()
