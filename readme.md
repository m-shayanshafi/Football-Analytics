##  Goal Prediction

This goal is to generate a model for predicting at runtime whether a shot will go inside the goal. 

We further use this prediction mechanism to estimate the expected Goal Value of the player. 

The model is built by combining features used to predict are obtained from the following papers:

1. [A network-based approach to evaluate the performance of
football teams](http://ceur-ws.org/Vol-1970/paper-07.pdf)
2. ["Quality vs. Quantity”: Improved Shot Prediction in Soccer using Strategic Features from Spatiotemporal Data](http://www.sloansportsconference.com/wp-content/uploads/2015/02/SSAC15-RP-Finalist-Quality-vs-Quantity.pdf)
3. [Creating space to shoot: quantifying spatial relative field goal
efficiency in basketball](https://www.degruyter.com/view/j/jqas.2014.10.issue-3/jqas-2013-0094/jqas-2013-0094.xml)

## Setup

1. Code is tested for python 3.4.3

2. Download data from here:
https://drive.google.com/open?id=0B9OXuKKy7pR1T1ZETzJNZm0xVnM

3. Run installation.sh using sudo:
	sudo bash installation.sh

4. To setup mysql server and create a database please follow the guide [here](https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-18-04) and [here](https://www.a2hosting.ca/kb/developer-corner/mysql/managing-mysql-databases-and-users-from-the-command-line).

5. Download the data file here:
https://drive.google.com/open?id=0B9OXuKKy7pR1T1ZETzJNZm0xVnM

6. Load the data file into mysql by using the command below:

```
mysql -u username -p database_name < file.sql
```

7. Run football.py, no sudo access required. Need to provide database access

```	
	python3 football.py <host> <user> <password> <database>
```
