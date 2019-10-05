#!/usr/bin/python
import pymysql
import statistics
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Circle
import numpy as np
import sys
import pickle
import math

successfullPass = [2,3,4,5,6,8,9,10,15,16,17,19,21,25,28,35,36,37,38,46,48,49,50,53,54,55]

def draw_network(G,pos,ax,sg=None):
	
    for n in G:
    	# print n
        c=Circle(pos[n],radius=0.005,alpha=0.5)
        ax.add_patch(c)
        G.node[n]['patch']=c
        x,y=pos[n]
    seen={}
    for (u,v,d) in G.edges(data=True):
        n1=G.node[u]['patch']
        n2=G.node[v]['patch']
        rad=0.1
        if (u,v) in seen:
            rad=seen.get((u,v))
            rad=(rad+np.sign(rad)*0.1)*-1
        alpha=0.5
        color='b'

        e = FancyArrowPatch(n1.center,n2.center,patchA=n1,patchB=n2,
                            arrowstyle='-|>',
                            connectionstyle='arc3,rad=%s'%rad,
                            mutation_scale=10.0,
                            lw=d['weight'],
                            alpha=alpha,
                            color=color)
        seen[(u,v)]=rad
        ax.add_patch(e)
    return e

# def fieldLimitBackup(cur):
# 	cur.execute("SELECT MIN(x1) FROM events WHERE event_type_id = 21 AND x1 > -10000 AND y1 > -10000")
# 	xMin = cur.fetchone()[0]
# 	cur.execute("SELECT MAX(x1) FROM events WHERE event_type_id = 21 AND x1 > -10000 AND y1 > -10000")
# 	xMax = cur.fetchone()[0]
# 	cur.execute("SELECT MIN(y1) FROM events WHERE event_type_id = 6 AND x1 > -10000 AND y1 > -10000")
# 	yMin = cur.fetchone()[0]
# 	cur.execute("SELECT MAX(y1) FROM events WHERE event_type_id = 6 AND x1 > -10000 AND y1 > -10000")
# 	yMax = cur.fetchone()[0]


# 	return xMin, xMax, yMin, yMax

# def fieldLimits(matchID, cur):
# 	cur.execute("SELECT MIN(x1) FROM events WHERE event_type_id = 21 AND x1 > -10000 AND y1 > -10000 AND match_id = %s", (matchID))
# 	xMin = cur.fetchone()[0]
	
# 	if (xMin is None or xMin >= 0):
# 		return fieldLimitBackup(cur)

# 	cur.execute("SELECT MAX(x1) FROM events WHERE event_type_id = 21 AND x1 > -10000 AND y1 > -10000 AND match_id = %s", (matchID))
# 	xMax = cur.fetchone()[0]

# 	if (xMax is None or xMax <= 0):
# 		return fieldLimitBackup(cur)

# 	cur.execute("SELECT MIN(y1) FROM events WHERE event_type_id = 6 AND x1 > -10000 AND y1 > -10000 AND match_id = %s", (matchID))
# 	yMin = cur.fetchone()[0]

# 	if (yMin is None or yMin >= 0):
# 		return fieldLimitBackup(cur)

# 	cur.execute("SELECT MAX(y1) FROM events WHERE event_type_id = 6 AND x1 > -10000 AND y1 > -10000 AND match_id = %s", (matchID))
# 	yMax = cur.fetchone()[0]

# 	if (yMax is None or yMax <= 0):
# 		return fieldLimitBackup(cur)

# 	return xMin, xMax, yMin, yMax

def fieldLimitBackup(cur):
	cur.execute("SELECT MIN(x1), MAX(x1) FROM events WHERE x1 > -10000 AND y1 > -10000 AND event_type_id IN (10,17,21,6)")
	row = cur.fetchone()
	xMin = row[0]
	xMax = row[1]

	cur.execute("SELECT MIN(y1), MAX(y1) FROM events WHERE x1 > -10000 AND y1 > -10000 AND event_type_id IN (10,17,21,6)")
	row = cur.fetchone()
	yMin = row[0]
	yMax = row[1]

	return xMin, xMax, yMin, yMax

def fieldLimits(matchID, cur):
	cur.execute("SELECT MIN(x1), MAX(x1) FROM events WHERE x1 > -10000 AND y1 > -10000 AND match_id=%s\
	 AND event_type_id IN (10,17,21)", (matchID))
	row = cur.fetchone()
	xMin = row[0]
	xMax = row[1]

	cur.execute("SELECT MIN(y1), MAX(y1) FROM events WHERE x1 > -10000 AND y1 > -10000 AND match_id=%s\
	 AND event_type_id IN (10,17,21,6)", (matchID))
	row = cur.fetchone()
	yMin = row[0]
	yMax = row[1]

	if xMin == None or xMax == None or yMin == None or yMax == None \
	or xMin >= 0 or xMax <= 0 or yMin >= 0 or yMax <= 0:
		xMin, xMax, yMin, yMax = fieldLimitBackup(cur)

	# print('xMin: ',xMin,' xMax: ',xMax,' yMin: ',yMin,' yMax: ',yMax )

	if xMin == None or xMax == None or yMin == None or yMax == None:
		print('Still getting None')
		sys.exit(0)

	return xMin, xMax, yMin, yMax

def playerZonalGraph(playerID, matches_teams, cur):
	f = open('playerZonalGraph.txt', 'wb')
	gridLength = 12
	gridWidth = 9

	passMap = nx.DiGraph()
	for i in range(gridLength):
		for j in range(gridWidth):
			# print str(j + gridLength*i)
			passMap.add_node(j + gridLength*i)

	for match_team in matches_teams:

		matchID = match_team[0]
		teamID = match_team[1]

		xMin, xMax, yMin, yMax = fieldLimits(matchID, cur)

		cur.execute("SELECT x2 FROM `events` WHERE match_id = %s AND player1_team_id = %s \
			AND match_half = 1 AND event_type_id IN (10,17)", (matchID,teamID))

		if (cur.rowcount == 0):
			continue

		goalLocation = cur.fetchone()[0]

		cur.execute("SELECT player_squads.player_id, events.event_type_id, events.match_time, events.match_half, events.x1, events.y1 \
			FROM events INNER JOIN player_squads ON events.player1_ps_id = player_squads.player_squad_id WHERE \
			match_id = %s AND player1_team_id = %s ORDER BY match_time ASC", (matchID, teamID))

		prev = (0,0,0,0,0)
		row = (0,0,0,0,0)
		prevNode = -1
		curNode = -1
		countPasses = 0
		# output = list(cur.fetchall())

		for x in range(cur.rowcount):
			prev = row
			row = cur.fetchone()
			if (row[1] in successfullPass and (row[4] < xMin or row[5] < yMin)):
				continue

			prevNode = curNode
			if ((row[3] == 1 and goalLocation > 0) or (row[3] == 2 and goalLocation < 0)):
				passLocation = 1
			else:
				passLocation = -1

			try:
				gridX = int(math.floor((((row[4]*passLocation) - xMin)*gridLength) / (xMax - xMin)))
			except Exception as E:
				# print 'Grid X: ' + str(gridX)
				# print 'Grid Y: ' + str(gridY)
				print('Max X: ' + str(xMax))
				print('Min X: ' + str(xMin))
				print('Max Y: ' + str(yMax))
				print('Min y: ' + str(yMin))
				print('Error in network File')
				sys.exit()
			gridY = int(math.floor((((row[5]*passLocation) - yMin)*gridWidth) / (yMax - yMin)))

			curNode = gridY + gridLength*gridX

			if (prev[1] == 2 and row[0] != prev[0] and (row[1] in successfullPass) \
				and (row[0] == playerID or prev[0] == playerID)):

				# if curNode < 0 or prevNode < 0:
				# 	print "Terminating here"
				# 	sys.exit(0)

				if (passMap.has_edge(prevNode,curNode)):
					countPasses += 1
					passMap[prevNode][curNode]['weight'] += 1
				else:
					countPasses += 1;
					passMap.add_edge(prevNode,curNode,weight=1)

		# print("Passes: " + str(countPasses))


	pickle.dump(passMap, f)
	f.close()
	# dg = pickle.load(open('playerZonalGraph.txt'))
	# edge_labels=dict([((u,v,),d['weight']) for u,v,d in passMap.edges(data=True)])
	# plt.figure(figsize=(100,100))
	# pos = nx.spring_layout(passMap)
	# ax=plt.gca()
	# # # nx.draw_networkx_labels(passMap,pos,font_size=10,font_family='sans-serif')
	# draw_network(passMap,pos,ax, edge_labels)
	# ax.autoscale()
	# plt.axis('equal')
	# plt.axis('off')
	# plt.savefig("graphzonal.png")
	# plt.show()

def playerPassGraph(playerID, matches_teams, cur):
	f = open('playerPassData.txt', 'w')
	passNetwork = []

	for match_team in matches_teams:
		matchID = match_team[0]
		teamID = match_team[1]
		Team = nx.DiGraph()

		cur.execute("SELECT player_squads.player_id, events.event_type_id, events.match_time FROM events \
			INNER JOIN player_squads ON events.player1_ps_id = player_squads.player_squad_id WHERE match_id = %s \
			AND player1_team_id = %s ORDER BY match_time ASC", (matchID, teamID))

		if (cur.rowcount == 0):
			continue

		prev = (0,0,0)
		row = (0,0,0)
		countPasses = 0
		output = list(cur.fetchall())
		nodes = list(set([y[0] for y in output]))

		for x in nodes:
			Team.add_node(x)

		for x in output:
			prev = row
			row = x

			if (prev[1] == 2 and row[0] != prev[0] and (row[1] in successfullPass) \
				and (row[0] == playerID or prev[0] == playerID)):

				if (Team.has_edge(prev[0],row[0])):
					countPasses += 1
					Team[prev[0]][row[0]]['weight'] += 1
				else:
					countPasses += 1;
					Team.add_edge(prev[0],row[0],weight=1)

		passInList = [i for _,j,i in  (Team.in_edges_iter(data='weight')) if j == playerID]
		passOutList = [i for _,j,i in  (Team.in_edges_iter(data='weight')) if j != playerID]
		passInList = [i['weight'] for i in passInList]
		passOutList = [i['weight'] for i in passOutList]

		try: 
			passInMean = statistics.mean(passInList)
			passOutMean = statistics.mean(passOutList)
			passInDev = statistics.stdev(passInList)
			passOutDev = statistics.stdev(passOutList)
		except:
			continue

		try: 
			harmonicIn = 2/((1/passInMean) + (1/passInDev))
		except:
			harmonicIn = 0

		try:
			harmonicOut = 2/((1/passOutMean) + (1/passOutDev))
		except:
			harmonicOut = 0

		passNetwork.append((matchID, teamID, playerID, passInMean,passInDev, harmonicIn, passOutMean,passOutDev,harmonicOut))
		f.write(str((matchID, teamID, playerID, passInMean,passInDev, harmonicIn, passOutMean,passOutDev,harmonicOut)))

		# edge_labels=dict([((u,v,),d['weight']) for u,v,d in Team.edges(data=True)])
		# plt.figure(figsize=(100,100))
		# pos = nx.spring_layout(Team)
		# ax=plt.gca()
		# # nx.draw_networkx_edge_labels(Team,pos,edge_cmap=plt.cm.Blues)
		# # nx.draw_networkx_nodes(Team,pos, node_size=500,edge_cmap=plt.cm.Reds)
		# nx.draw_networkx_labels(Team,pos,font_size=10,font_family='sans-serif')
		# draw_network(Team,pos,ax, edge_labels)
		
		# ax.autoscale()
		# plt.axis('equal')
		# plt.axis('off')
		# plt.savefig("graph.png")
		# plt.show()
		# print "Team Passes: " + str(countPasses)
		# plt.show()
		# sys.exit(0)

	f.close()
