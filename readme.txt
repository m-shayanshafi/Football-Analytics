1. Code is tested for python 3.4.3

2. Download data from here:
https://drive.google.com/open?id=0B9OXuKKy7pR1T1ZETzJNZm0xVnM

3. Run installation.sh using sudo:
	sudo bash installation.sh

4. To setup mysql server please follow the guide here:
https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-18-04

5. Download the data file here:
https://drive.google.com/open?id=0B9OXuKKy7pR1T1ZETzJNZm0xVnM

6. Load the data file into mysql by using the command below:
mysql -u username -p database_name < file.sql

7. Run football.py, no sudo access required. Need to provide database access
	python3 football.py <host> <user> <password> <database>