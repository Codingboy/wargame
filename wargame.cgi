#!/usr/bin/env python3.4
#pip install Flask

import sqlite3
import os
import random
import logging
import hashlib
import json
import re
import sys
from flask import Flask, request, redirect, session, abort, jsonify, url_for
from werkzeug.serving import run_simple
from wsgiref.handlers import CGIHandler
#from flup.server.fcgi import WSGIServer

host = "192.168.2.105"
port = 8080

PROJECTNAME = "WargameTournament"
DBNAME = PROJECTNAME+".sqlite"

logger = logging.getLogger(PROJECTNAME)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(PROJECTNAME+".log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

app = Flask(__name__)
UPLOAD_FOLDER = "./static/"
ALLOWED_EXTENSIONS = set([".wargamerpl2"])
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

connection = sqlite3.connect(DBNAME)
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER, user TEXT, password TEXT, permissions INTEGER, PRIMARY KEY(id))")
if (cursor.execute("SELECT Count(*) FROM users WHERE user='admin'").fetchone()[0] == 0):
	cursor.execute("INSERT INTO users (user, password, permissions) VALUES('admin', 'BlaBlub42', 42)")
if (cursor.execute("SELECT Count(*) FROM users WHERE user='Admin'").fetchone()[0] == 0):
	cursor.execute("INSERT INTO users (user, password, permissions) VALUES('Admin', 'BlaBlub42', 42)")
if (cursor.execute("SELECT Count(*) FROM users WHERE user='Guest'").fetchone()[0] == 0):
	cursor.execute("INSERT INTO users (user, password, permissions) VALUES('Guest', '42', 0)")
if (cursor.execute("SELECT Count(*) FROM users WHERE user='guest'").fetchone()[0] == 0):
	cursor.execute("INSERT INTO users (user, password, permissions) VALUES('guest', '42', 0)")
cursor.execute("CREATE TABLE IF NOT EXISTS tournaments(id INTEGER, name TEXT, PRIMARY KEY(id))")
cursor.execute("CREATE TABLE IF NOT EXISTS participates(userID INTEGER, tournamentID INTEGER, PRIMARY KEY(userID, tournamentID))")
cursor.execute("CREATE TABLE IF NOT EXISTS matches(id INTEGER, tournamentID INTEGER, userID1 INTEGER, userID2 INTEGER, deck1 TEXT, deck2 TEXT, replay TEXT, winner INTEGER, map TEXT, PRIMARY KEY(id))")
connection.commit()
connection.close()

@app.route("/", methods=["GET"])
def root():
	connection = sqlite3.connect(DBNAME)
	cursor = connection.cursor()
	dbEntry = cursor.execute("SELECT id FROM tournaments ORDER BY id DESC").fetchone()
	tournamentID = dbEntry[0]
	connection.close()
	return redirect(request.url_root+"tournament/"+str(tournamentID), code=302)

@app.route("/createTournament", methods=["POST"])
def createTournament():
	if (getPermissions() < 42):
		return abort(401)
	if request.method == "POST":
		if ("name" in request.form):
			name = request.form["name"]
			connection = sqlite3.connect(DBNAME)
			cursor = connection.cursor()
			cursor.execute("INSERT INTO tournaments (name) VALUES(?)", (name,))
			connection.commit()
			connection.close()
			logging.getLogger(PROJECTNAME).info("tournament created")
			return redirect(request.url_root, code=302)

def parseReplay(path):
	ret = []
	if (os.path.isfile(path)):
		file = open(path, "rb")
		line = file.readline()
		first = 0
		last = 0
		for i in range(0, (len(line)-1)):
			if (line[i] == 123):
				first = i
				break
		for i in range(0, (len(line)-1)):
			if (line[len(line)-1-i] == 125 and line[len(line)-1-i-1] == 125):
				last = len(line)-i
				break
		line = line[first:last]
		line = line.decode("utf-8")
		parsed = json.loads(line)
		deck1 = ""
		deck2 = ""
		user1 = ""
		user2 = ""
		startMoney = parsed["game"]["InitMoney"]
		gameMode = parsed["game"]["GameMode"]
		field = parsed["game"]["Map"]
		gameType = parsed["game"]["GameType"]
		timeLimit = parsed["game"]["TimeLimit"]
		conquestPoints = parsed["game"]["ScoreLimit"]
		income = parsed["game"]["IncomeRate"]
		if (startMoney != "1000" or gameMode != "1" or field not in ["Conquete_2x2_port_Wonsan_Terrestre","Conquete_3x3_Muju","Conquete_2x3_Montagne_1","Conquete_2x3_Gangjin","Conquete_2x3_Tohoku_Alt","Conquete_2x3_Hwaseong"] or timeLimit != "3600" or gameType != "1" or conquestPoints != "500" or income != "1"):
			return []
		for i in range(0,20):
			if ("player_"+str(i) in parsed):
				player = parsed["player_"+str(i)]
				ready = player["PlayerReady"]
				if (not ready):
					pass#return []
				if (user1 == ""):
					user1 = player["PlayerName"]
					deck1 = player["PlayerDeckContent"]
				else:
					user2 = player["PlayerName"]
					deck2 = player["PlayerDeckContent"]
					break
		file.close()
		ret = [[user1,deck1],[user2,deck2]]
	return ret

@app.route("/impressum", methods=["GET"])
def impressum():
	html = beginHTML(request)
	html += "\
<div class='impressum'><h1>Impressum</h1><p>Angaben gemäß § 5 TMG</p><p>Daniel Tkocz <br> \n\
Schiffergasse 15<br> \n\
65201 Wiesbaden <br> \n\
</p><p> <strong>Vertreten durch: </strong><br>\n\
Daniel Tkocz<br>\n\
</p><p><strong>Kontakt:</strong> <br>\n\
Telefon: 0611-609534<br>\n\
E-Mail: <a href='mailto:daniel.tkocz42@gmail.com'>daniel.tkocz42@gmail.com</a></br></p><p><strong>Haftungsausschluss: </strong><br><br><strong>Haftung für Inhalte</strong><br><br>\n\
Die Inhalte unserer Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen. Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen. Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung möglich. Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese Inhalte umgehend entfernen.<br><br><strong>Haftung für Links</strong><br><br>\n\
Unser Angebot enthält Links zu externen Webseiten Dritter, auf deren Inhalte wir keinen Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich. Die verlinkten Seiten wurden zum Zeitpunkt der Verlinkung auf mögliche Rechtsverstöße überprüft. Rechtswidrige Inhalte waren zum Zeitpunkt der Verlinkung nicht erkennbar. Eine permanente inhaltliche Kontrolle der verlinkten Seiten ist jedoch ohne konkrete Anhaltspunkte einer Rechtsverletzung nicht zumutbar. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen.<br><br><strong>Urheberrecht</strong><br><br>\n\
Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers. Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet. Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die Urheberrechte Dritter beachtet. Insbesondere werden Inhalte Dritter als solche gekennzeichnet. Sollten Sie trotzdem auf eine Urheberrechtsverletzung aufmerksam werden, bitten wir um einen entsprechenden Hinweis. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Inhalte umgehend entfernen.<br><br><strong>Datenschutz</strong><br><br>\n\
Die Nutzung unserer Webseite ist in der Regel ohne Angabe personenbezogener Daten möglich. Soweit auf unseren Seiten personenbezogene Daten (beispielsweise Name, Anschrift oder eMail-Adressen) erhoben werden, erfolgt dies, soweit möglich, stets auf freiwilliger Basis. Diese Daten werden ohne Ihre ausdrückliche Zustimmung nicht an Dritte weitergegeben. <br>\n\
Wir weisen darauf hin, dass die Datenübertragung im Internet (z.B. bei der Kommunikation per E-Mail) Sicherheitslücken aufweisen kann. Ein lückenloser Schutz der Daten vor dem Zugriff durch Dritte ist nicht möglich. <br>\n\
Der Nutzung von im Rahmen der Impressumspflicht veröffentlichten Kontaktdaten durch Dritte zur Übersendung von nicht ausdrücklich angeforderter Werbung und Informationsmaterialien wird hiermit ausdrücklich widersprochen. Die Betreiber der Seiten behalten sich ausdrücklich rechtliche Schritte im Falle der unverlangten Zusendung von Werbeinformationen, etwa durch Spam-Mails, vor.<br>\n\
</p><br> \n\
Website Impressum erstellt durch <a href='http://www.impressum-generator.de'>impressum-generator.de</a> von der <a href='http://www.kanzlei-hasselbach.de/standorte/koeln-rodenkirchen'>Kanzlei Hasselbach, Köln-Rodenkirchen</a> </div>\n"
	html += "\
	</body>\n\
</html>\n"
	return html
 
def navBar(request):
	html = "\
		<nav class='navbar navbar-default navbar-fixed-top'>\n\
			<div class='container'>\n\
				<div class='navbar-header'>\n\
			  		<button type='button' class='navbar-toggle collapsed' data-toggle='collapse' data-target='#navbar' aria-expanded='false' aria-controls='navbar'>\n\
						<span class='sr-only'>Toggle navigation</span>\n\
						<span class='icon-bar'></span>\n\
						<span class='icon-bar'></span>\n\
						<span class='icon-bar'></span>\n\
					</button>\n\
					<a class='navbar-brand' href='"+request.url_root+"'>Wargame Turnier</a>\n\
				</div>\n\
				<div id='navbar' class='navbar-collapse collapse'>\n\
					<ul class='nav navbar-nav'>\n\
						<li><a href='"+request.url_root+"impressum'>Impressum</a></li>\n\
						<li><a href='"+request.url_root+"rules'>Regeln</a></li>\n\
						<li class='Tournaments'>\n\
							<a href='#' class='dropdown-toggle' data-toggle='dropdown' role='button' aria-haspopup='true' aria-expanded='false'>Turniere <span class='caret'></span></a>\n\
							<ul class='dropdown-menu'>\n"
	connection = sqlite3.connect(DBNAME)
	cursor = connection.cursor()
	dbEntries = cursor.execute("SELECT name,id FROM tournaments").fetchall()
	for dbEntry in dbEntries:
		html += "\
								<li><a href='"+request.url_root+"tournament/"+str(dbEntry[1])+"'>"+dbEntry[0]+"</a></li>\n"
	connection.close()
	html += "\
							</ul>\n\
						</li>\n\
						<li><a href='https://aqarius90.github.io/FA_WG_Utilities/'>Deckeditor</a></li>\n\
			 		</ul>\n"
	if (getPermissions() >= 42):
		html += "\
					<form class='navbar-form navbar-nav' action='"+request.url_root+"createTournament' method='post'>\n\
						<div class='form-group'>\n\
							<input type='text' placeholder='Tournament' class='form-control' name='name'>\n\
						</div>\n\
						<button type='submit' class='btn btn-success'>Erstellen</button>\n\
					</form>\n"
	if (getPermissions() == 0):
		html += "\
					<ul class='nav navbar-right'>\n\
						<li><a href='"+request.url_root+"register'>Registrieren</a></li>\n\
					</ul>\n\
					<form class='navbar-form navbar-right' action='"+request.url_root+"login' method='post'>\n\
						<div class='form-group'>\n\
							<input type='text' placeholder='User' class='form-control' name='user'>\n\
						</div>\n\
						<div class='form-group'>\n\
							<input type='password' placeholder='Password' class='form-control' name='password'>\n\
						</div>\n\
						<button type='submit' class='btn btn-success'>Anmelden</button>\n\
					</form>\n"
	else:
		html += "\
					<ul class='nav navbar-right'>\n\
						<li><a href='"+request.url_root+"logout'>Abmelden</a></li>\n\
					</ul>\n"
	html += "\
				</div><!--/.nav-collapse -->\n\
			</div>\n\
		</nav>\n"
	return html

def beginHTML(request):
	html = "\
<html>\n\
	<head>\n\
		<meta charset='utf-8'>\n\
		<meta http-equiv='X-UA-Compatible' content='IE=edge'>\n\
		<meta name='viewport' content='width=device-width, initial-scale=1'>\n\
		<link href='"+request.url_root+"static/css/bootstrap.min.css' rel='stylesheet'>\n\
		<link href='https://cdn.datatables.net/1.10.13/css/dataTables.bootstrap4.min.css' rel='stylesheet'>\n\
		<style>\n\
			body\n\
			{\n\
				padding-top: 5%;\n\
				padding-right: 7.5%;\n\
				padding-bottom: 5%;\n\
				padding-left: 7.5%;\n\
			}\n\
		</style>\n\
		<title>Tournament</title>\n\
	</head>\n\
	<body>\n\
		<script src='https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js'></script>\n\
		<script src='"+request.url_root+"static/js/bootstrap.min.js'></script>\n\
		<script src='https://cdn.datatables.net/1.10.13/js/jquery.dataTables.min.js'></script>\n\
		<script src='https://cdn.datatables.net/1.10.13/js/dataTables.bootstrap4.min.js'></script>\n"
	html += navBar(request)
	html += "\
		<br/>\n"
	return html


@app.route("/tournament/<int:tournamentID>", methods=["GET", "POST"])
def tournament(tournamentID):
	if request.method == "POST":
		if (getPermissions() > 0):
			connection = sqlite3.connect(DBNAME)
			cursor = connection.cursor()
			userID = cursor.execute("SELECT id FROM users WHERE user=?", (getUser(),)).fetchone()[0]
			dbEntries = cursor.execute("SELECT userID FROM participates WHERE tournamentID=?", (tournamentID,)).fetchall()
			myMaps = {"Mud Fight !":0,"Nuclear Winter is coming":0,"Wonsan harbour":0,"Plunjing Valley":0,"Death Row":0,"Paddy Field":0}
			for dbEntry in dbEntries:
				conn = sqlite3.connect(DBNAME)
				cur = conn.cursor()
				maps = {"Mud Fight !":0,"Nuclear Winter is coming":0,"Wonsan harbour":0,"Plunjing Valley":0,"Death Row":0,"Paddy Field":0}
				entries = cur.execute("SELECT map FROM matches WHERE tournamentID=? AND (userID1=? OR userID2=?)", (tournamentID,dbEntry[0],dbEntry[0],)).fetchall()
				for entry in entries:
					maps[entry[0]] = maps[entry[0]] + 1
				for key in myMaps:
					maps[key] = maps[key] + myMaps[key]
				minimum = sys.maxsize
				for key in maps:
					if (maps[key] < minimum):
						minimum = maps[key]
				mapSelection = []
				for key in maps:
					if (maps[key] == minimum):
						mapSelection.append(key)
				randomMap = random.choice(mapSelection)
				myMaps[randomMap] = myMaps[randomMap] + 1
				conn.close()
				cursor.execute("INSERT INTO matches (tournamentID, userID1, userID2, winner, deck1, deck2, map, replay) VALUES(?, ?, ?, -1, '', '', ?, '')", (tournamentID, userID, dbEntry[0], randomMap,))
			cursor.execute("INSERT INTO participates (tournamentID, userID) VALUES(?, ?)", (tournamentID, userID,))
			connection.commit()
			connection.close()
			logging.getLogger(PROJECTNAME).info(str(userID)+" participates in "+str(tournamentID))
	html = beginHTML(request)
	if (getPermissions() > 0):
		connection = sqlite3.connect(DBNAME)
		cursor = connection.cursor()
		userID = cursor.execute("SELECT id FROM users WHERE user=?", (getUser(),)).fetchone()[0]
		if (cursor.execute("SELECT Count(*) FROM participates WHERE userID=? AND tournamentID=?", (userID, tournamentID,)).fetchone()[0] == 0):
			html += "\
		<form action='' method='post'>\n\
			<input type='submit' value='Teilnehmen'><br/>\n\
		</form>\n"
	html += "\
		<div class='bs-example bs-example-tabs' data-example-id=togglable-tabs>\n\
			<ul class='nav nav-tabs' id=myTabs role=tablist>\n\
				<li role=presentation class=active>\n\
					<a href=#overview id=overview-tab role=tab data-toggle=tab aria-controls=overview aria-expanded=true>Übersicht</a>\n\
				</li>\n"
	if (getPermissions() > 0):
		html += "\
				<li role=presentation>\n\
					<a href=#myMatches role=tab id=myMatches-tab data-toggle=tab aria-controls=myMatches>Meine Spiele</a>\n\
				</li>\n"
	html += "\
				<li role=presentation>\n\
					<a href=#allMatches role=tab id=allMatches-tab data-toggle=tab aria-controls=allMatches>Alle Spiele</a>\n\
				</li>\n\
			</ul>\n\
			<div class=tab-content id=myTabContent>\n\
				<div class='tab-pane fade in active' role=tabpanel id=overview aria-labelledby=overview-tab>\n\
					<script type='text/javascript' class='init'>\n\
						$(document).ready(function() {\n\
							$('#table1').DataTable({'order':[[4,'desc']]});\n\
						} );\n\
					</script>\n\
					<table id='table1' class='table table-striped'>\n\
						<thead>\n\
							<tr>\n\
								<th>\n\
									Spieler\n\
								</th>\n\
								<th>\n\
									Siege\n\
								</th>\n\
								<th>\n\
									Unentschieden\n\
								</th>\n\
								<th>\n\
									Niederlagen\n\
								</th>\n\
								<th>\n\
									Punkte\n\
								</th>\n\
								<th>\n\
									Spiele\n\
								</th>\n\
								<th>\n\
									Punkte/Spiel\n\
								</th>\n\
							</tr>\n\
						</thead>\n\
						<tbody>\n"
	connection = sqlite3.connect(DBNAME)
	cursor = connection.cursor()
	dbEntries = cursor.execute("SELECT users.user,users.id FROM users,participates WHERE participates.tournamentID=? AND participates.userID=users.id", (tournamentID,)).fetchall()
	for dbEntry in dbEntries:
		user = dbEntry[0]
		userID = dbEntry[1]
		conn = sqlite3.connect(DBNAME)
		cur = conn.cursor()
		win = cur.execute("SELECT Count(*) from matches WHERE tournamentID=? AND winner=?", (tournamentID,userID,)).fetchone()[0]
		draw = cur.execute("SELECT Count(*) from matches WHERE tournamentID=? AND winner=0", (tournamentID,)).fetchone()[0]
		lose = cur.execute("SELECT Count(*) from matches WHERE tournamentID=? AND ((winner=userID1 AND userID2=?) OR (winner=userID2 AND userID1=?))", (tournamentID,userID,userID,)).fetchone()[0]
		conn.close()
		points = 2*win+1*draw+0*lose
		matches = win+draw+lose
		ppm = 0
		if (matches > 0):
			ppm = points/matches
		conn.close()
		html += "\
							<tr>\n\
								<td>\n\
									"+user+"\n\
								</td>\n\
								<td>\n\
									"+str(win)+"\n\
								</td>\n\
								<td>\n\
									"+str(draw)+"\n\
								</td>\n\
								<td>\n\
									"+str(lose)+"\n\
								</td>\n\
								<td>\n\
									"+str(points)+"\n\
								</td>\n\
								<td>\n\
									"+str(matches)+"\n\
								</td>\n\
								<td>\n\
									"+str(ppm)+"\n\
								</td>\n\
							</tr>\n"
	html += "\
						</tbody>\n\
					</table>\n\
				</div>\n\
		<script>\n\
			document.addEventListener('click', function(e)\n\
			{\n\
				e = e || window.event;\n\
				var target = e.target || e.srcElement,\n\
				text = target.textContent || text.innerText;\n\
				text = target.title;\n\
				if (text != \"\")\n\
				{\n\
					window.open('https://aqarius90.github.io/FA_WG_Utilities/?='+text, '_self');\n\
				}\n\
			}, false);\n\
		</script>\n"
	if (getPermissions() > 0):
		html += "\
				<div class='tab-pane fade' role=tabpanel id=myMatches aria-labelledby=myMatches-tab>\n\
					<script type='text/javascript' class='init'>\n\
						$(document).ready(function() {\n\
							$('#table2').DataTable();\n\
						} );\n\
					</script>\n\
					<table id='table2' class='table table-striped'>\n\
						<thead>\n\
							<tr>\n\
								<th>\n\
									Spieler1\n\
								</th>\n\
								<th>\n\
									Spieler2\n\
								</th>\n\
								<th>\n\
									Karte\n\
								</th>\n\
								<th>\n\
									Sieger\n\
								</th>\n\
								<th>\n\
									Replay\n\
								</th>\n\
							</tr>\n\
						</thead>\n\
						<tbody>\n"
		dbEntries = cursor.execute("SELECT u1.user,matches.deck1,u2.user,matches.deck2,matches.map,matches.winner,matches.replay,matches.id,u1.id,u2.id FROM users as u1,users as u2,matches WHERE matches.tournamentID=? AND u1.id=matches.userID1 AND u2.id=matches.userID2 AND (u1.user=? OR u2.user=?)", (tournamentID,getUser(),getUser(),)).fetchall()
		for dbEntry in dbEntries:
			html += "\
							<tr>\n\
								<td title='"+dbEntry[1]+"'>\n\
									"+dbEntry[0]+"\n\
								</td>\n\
								<td title='"+dbEntry[3]+"'>\n\
									"+dbEntry[2]+"\n\
								</td>\n\
								<td>\n\
									"+dbEntry[4]+"\n\
								</td>\n\
								<td>\n"
			winner = "Ausstehend"
			if (dbEntry[5] == dbEntry[8]):
				winner = dbEntry[0]
			if (dbEntry[5] == dbEntry[9]):
				winner = dbEntry[2]
			if (dbEntry[5] == 0):
				winner = "Unentschieden"
			if (getUser() == dbEntry[0] or getUser() == dbEntry[2] or getPermissions() >= 42):
				html += "\
									<a href='"+request.url_root+"match/"+str(dbEntry[7])+"'>"+winner+"</a>\n"
			else:
				html += "\
									"+winner+"\n"
			replay = ""
			if (dbEntry[6] != ""):
				replay = "<a href='"+request.url_root+app.config["UPLOAD_FOLDER"]+dbEntry[6]+"'>Herunterladen</a>"
			html += "\
								</td>\n\
								<td>\n\
									"+replay+"\n\
								</td>\n\
							</tr>\n"
		html += "\
						</tbody>\n\
					</table>\n\
				</div>\n"
	html += "\
				<div class='tab-pane fade' role=tabpanel id=allMatches aria-labelledby=allMatches-tab>\n\
					<script type='text/javascript' class='init'>\n\
						$(document).ready(function() {\n\
							$('#table3').DataTable();\n\
						} );\n\
					</script>\n\
					<table id='table3' class='table table-striped'>\n\
						<thead>\n\
							<tr>\n\
								<th>\n\
									Spieler1\n\
								</th>\n\
								<th>\n\
									Spieler2\n\
								</th>\n\
								<th>\n\
									Karte\n\
								</th>\n\
								<th>\n\
									Sieger\n\
								</th>\n\
								<th>\n\
									Replay\n\
								</th>\n\
							</tr>\n\
						</thead>\n\
						<tbody>\n"
	dbEntries = cursor.execute("SELECT u1.user,matches.deck1,u2.user,matches.deck2,matches.map,matches.winner,matches.replay,matches.id,u1.id,u2.id FROM users as u1,users as u2,matches WHERE matches.tournamentID=? AND u1.id=matches.userID1 AND u2.id=matches.userID2", (tournamentID,)).fetchall()
	for dbEntry in dbEntries:
		html += "\
							<tr>\n\
								<td title='"+dbEntry[1]+"'>\n\
									"+dbEntry[0]+"\n\
								</td>\n\
								<td title='"+dbEntry[3]+"'>\n\
									"+dbEntry[2]+"\n\
								</td>\n\
								<td>\n\
									"+dbEntry[4]+"\n\
								</td>\n\
								<td>\n"
		winner = "Ausstehend"
		if (dbEntry[5] == dbEntry[8]):
			winner = dbEntry[0]
		if (dbEntry[5] == dbEntry[9]):
			winner = dbEntry[2]
		if (dbEntry[5] == 0):
			winner = "Unentschieden"
		if (getUser() == dbEntry[0] or getUser() == dbEntry[2] or getPermissions() >= 42):
			html += "\
									<a href='"+request.url_root+"match/"+str(dbEntry[7])+"'>"+winner+"</a>\n"
		else:
			html += "\
									"+winner+"\n"
		replay = ""
		if (dbEntry[6] != ""):
			replay = "<a href='"+request.url_root+app.config["UPLOAD_FOLDER"]+dbEntry[6]+"'>Herunterladen</a>"
		html += "\
								</td>\n\
								<td>\n\
									"+replay+"\n\
								</td>\n\
							</tr>\n"
	html += "\
						</tbody>\n\
					</table>\n\
				</div>\n\
			</div>\n\
		</div>\n"
	connection.close()
	html += "\
	</body>\n\
</html>\n"
	return html

@app.route("/match/<int:matchID>", methods=["GET", "POST"])
def match(matchID):
	connection = sqlite3.connect(DBNAME)
	cursor = connection.cursor()
	dbEntry = cursor.execute("SELECT u1.user,u1.id,u2.user,u2.id,matches.tournamentID FROM matches,users as u1,users as u2 WHERE matches.id=? AND u1.id=matches.userID1 AND u2.id=matches.userID2", (matchID,)).fetchone()
	userID1 = dbEntry[1]
	userID2 = dbEntry[3]
	user1 = dbEntry[0]
	user2 = dbEntry[2]
	tournamentID = dbEntry[4]
	connection.close()
	if (getUser() != user1 and getUser() != user2 and getPermissions() < 42):
		abort(401)
	if request.method == "POST":
		if ("winner" not in request.form or "replay" not in request.files):
			abort(400)
		winner = request.form["winner"]
		replay = request.files["replay"]
		if (replay.filename != ""):
			replay.save(os.path.join(app.config["UPLOAD_FOLDER"], str(tournamentID)+"_"+user1+"_"+user2+".wargamerpl2"))
			replayData = parseReplay(app.config["UPLOAD_FOLDER"]+str(tournamentID)+"_"+user1+"_"+user2+".wargamerpl2")
			deck1 = ""
			deck2 = ""
			for data in replayData:
				if (data[0] == user1):
					deck1 = data[1]
				if (data[0] == user2):
					deck2 = data[1]
			if (deck2 == "" or deck1 == ""):
				return error("Das hochgeladene Replay entspricht nicht den Regeln.")
		connection = sqlite3.connect(DBNAME)
		cursor = connection.cursor()
		cursor.execute("UPDATE matches SET winner=?, replay=?, deck1=?, deck2=? WHERE id=?", (winner,str(tournamentID)+"_"+user1+"_"+user2+".wargamerpl2",deck1,deck2,matchID,))
		connection.commit()
		connection.close()
		return redirect(request.url_root+"tournament/"+str(tournamentID), code=302)
	html = beginHTML(request)
	html += "\
		<form action='' method='post' enctype='multipart/form-data'>\n\
			<div class='form-group'>\n\
				<label for='winner'>Sieger</label>\n\
				<select name='winner' id='winner'>\n\
					<option value=''></option>\n\
					<option value='-1'>Ausstehend</option>\n\
					<option value='0'>Unentschieden</option>\n\
					<option value='"+str(userID1)+"'>"+user1+"</option>\n\
					<option value='"+str(userID2)+"'>"+user2+"</option>\n\
				</select>\
			</div>\n\
			<div class='form-group'>\n\
				<label for='replay'>Replay</label>\n\
				<input type='file' id='file' name='replay' accept='.wargamerpl2'>\n\
			</div>\n\
			<button type='submit' class='btn btn-default'>Senden</button>\n\
		</form>\n\
	</body>\n\
</html>\n"
	return html

def error(message, statusCode=400):
	response = jsonify({'message': message})
	response.status_code = statusCode
	return response

def getPermissions():
	permissions = 0
	if ("permissions" in session):
		permissions = session["permissions"]
	return permissions

def getUser():
	user = "Guest"
	if ("user" in session):
		user = session["user"]
	return user

@app.route("/login", methods=["POST"])
def login():
	if request.method == "POST":
		if ("user" in request.form and "password" in request.form):
			user = request.form["user"]
			password = request.form["password"]
			""""h = hashlib.new("sha256")
			h.update(request.form["password"].encode("utf-8"))
			password = h.hexdigest()"""
			connection = sqlite3.connect(DBNAME)
			cursor = connection.cursor()
			if (cursor.execute("SELECT Count(*) FROM users WHERE user=?", (user,)).fetchone()[0] > 0):
				dbEntry = cursor.execute("SELECT password,permissions FROM users WHERE user=?", (user,))
				row = dbEntry.fetchone()
				pw = row[0]
				permissions = row[1]
				connection.close()
				if (pw == password):
					session["user"] = user
					session["permissions"] = permissions
					logging.getLogger(PROJECTNAME).info(user+" logged in")
					return redirect(redirect_url(), code=302)
				else:
					logging.getLogger(PROJECTNAME).warning(user+" tried to log in")
					return redirect(redirect_url(), code=302)
			else:
				return redirect(redirect_url(), code=302)

def redirect_url(default='index'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)

@app.route("/logout", methods=["GET", "POST"])
def logout():
	logging.getLogger(PROJECTNAME).info(session["user"]+" logged out")
	session.pop("user", None)
	session.pop("permissions", None)
	return redirect(redirect_url(), code=302)

@app.route("/register", methods=["GET", "POST"])
def register():
	if request.method == "POST":
		if ("user" in request.form and "password" in request.form and "password2" in request.form):
			user = request.form["user"]
			password = request.form["password"]
			password2 = request.form["password2"]
			connection = sqlite3.connect(DBNAME)
			cursor = connection.cursor()
			userCount = cursor.execute("SELECT Count(*) FROM users WHERE user=?", (user,)).fetchone()[0]
			connection.close()
			if (userCount == 0 and password == password2 and re.match("^[a-zA-Z0-9]+$", user) is not None):
				""""h = hashlib.new("sha256")
				h.update(request.form["password"].encode("utf-8"))
				password = h.hexdigest()"""
				connection = sqlite3.connect(DBNAME)
				cursor = connection.cursor()
				cursor.execute("INSERT INTO users (user, password, permissions) VALUES(?, ?, 1)", (user, password,))
				connection.commit()
				connection.close()
				logging.getLogger(PROJECTNAME).info(user+" registered")
				session["user"] = user
				session["permissions"] = 1
				return redirect(request.url_root, code=302)
			else:
				logging.getLogger(PROJECTNAME).info(user+" tried to register")
				return redirect(request.url_root+"register", code=302)
	html = beginHTML(request)
	html += "\
		<div class='container'>\n\
			<div class='row'>\n\
				<div class='col-sx-4'/>\n\
				<div class='col-sx-4'>\n\
					<form action='' method='post'>\n\
						<div class='form-group'>\n\
							<label for='user'>Benutzer</label>\n\
							<input type='text' class='form-control' id='user' name='user' placeholder='Benutzer (a-zA-Z0-9)'>\n\
						</div>\n\
						<div class='form-group'>\n\
							<label for='password'>Passwort</label>\n\
							<input type='password' class='form-control' id='password' name='password' placeholder='Passwort'>\n\
						</div>\n\
						<div class='form-group'>\n\
							<label for='passwordRepeat'>Passwort wiederholen</label>\n\
							<input type='password' class='form-control' id='passwordRepeat' name='password2' placeholder='Passwort'>\n\
						</div>\n\
						<button type='submit' class='btn btn-default'>Registrieren</button>\n\
					</form>\n\
				</div>\n\
				<div class='col-sx-4'/>\n\
			</div>\n\
		</div>\n\
	</body>\n\
</html>\n"
	return html

@app.route("/deck", methods=["GET"])
def deck():
	html = beginHTML(request)
	html += "\
		<form action='' method='post'>\n\
			<div class='form-group'>\n\
				<label for='deck'>Deck</label>\n\
				<input type='text' class='form-control' id='deck' name='deck' placeholder='Deck'>\n\
			</div>\n\
			<button type='submit' class='btn btn-default'>Parse</button>\n\
		</form>\n\
		<script>\n\
			function bla(){\n\
				var newWin = window.open('https://aqarius90.github.io/FA_WG_Utilities/');\n\
				newWin.document.getElementById('sDeckString').value = '@Ho8J2ggcyPWcRU6ZKUlhEBvA1GALQDAJkpgEzwG4YuVBEHpKKWxxZyKiVxBH6JMQfBZqWAFYhZJR8i9knsWWiClQiKAieFKKJaA=';\n\
				newWin.onload = function(newWin)\n\
				{\n\
					newWin.document.getElementById('sDeckString').value = '@Ho8J2ggcyPWcRU6ZKUlhEBvA1GALQDAJkpgEzwG4YuVBEHpKKWxxZyKiVxBH6JMQfBZqWAFYhZJR8i9knsWWiClQiKAieFKKJaA=';\n\
				}\n\
			}\n\
		</script>\n\
		<script>document.onload = bla();</script>\n\
	</body>\n\
</html>\n"
	return html


@app.route("/rules", methods=["GET"])
def rules():
	html = beginHTML(request)
	html += "\
		<h3>Map</h3>\n\
		<p>\n\
		Die gespielte Map muss eine der folgenden sein:<br/>\n\
		Mud Fight !<br/>\n\
		Nuclear Winter is coming<br/>\n\
		Wonsan harbour<br/>\n\
		Plunjing Valley<br/>\n\
		Death Row<br/>\n\
		Paddy Field<br/>\n\
		<br/>\n\
		Jedem Match ist zufällig eine Map zugewiesen, die gespielt werden muss.<br/>\n\
		</p>\n\
		<hr/>\n\
		<h3>Deck</h3>\n\
		<p>\n\
		Vor jedem Matchbeginn ist sich auf ein zu spielendes Deck festzulegen.<br/>\n\
		Sobald das Deck für ein Match festgelegt ist, ist eine Änderung des Decks für das jeweilige Match ausgeschlossen.<br/>\n\
		Vor Matchbeginn ist dem Opponenten das eigene Deck zwecks Begutachtung zur Verfügung zu stellen.<br/>\n\
		</p>\n\
		<hr/>\n\
		<h3>Spieleinstellungen</h3>\n\
		<p>\n\
		Battlefield: siehe Map<br/>\n\
		Game mode: conquest<br/>\n\
		Opposition: so zu wählen, dass beide Spieler ihre festgelegten Decks wählen können<br/>\n\
		Accessibility: private<br/>\n\
		Starting points: 1000<br/>\n\
		Conquest points: 500<br/>\n\
		Time limit: 60 min<br/>\n\
		Income rate: Very low (4)<br/>\n\
		</p>\n\
		<hr/>\n\
		<h3>Fairness</h3>\n\
		<p>\n\
		Es ist auf Fairplay zu achten.<br/>\n\
		Insbesondere Helirushs sind zu unterlassen und können zum Ausschluss aus dem Turnier führen.<br/>\n\
		Bei Matchbeginn ist dem Opponenten ausreichend Zeit für die Aufstellung einzuräumen.<br/>\n\
		</p>\n\
		<hr/>\n\
		<h3>Ergebnis</h3>\n\
		<p>\n\
		Erreicht man die Zerstörung aller feindlichen CVs oder<br/>\n\
		erreicht die vorgegebene Anzahl an Conquestpunkten oder<br/>\n\
		der Opponent gibt auf oder<br/>\n\
		das Zeitlimit endet und man hat mehr Conquestpunkte als der Opponent dann<br/>\n\
		wird dies als Sieg gewertet.<br/>\n\
		Endet das Zeitlimit und man hat die gleiche Anzahl an Conquestpunkten wie der Opponent dann<br/>\n\
		wird dies als Unentschieden gewertet.<br/>\n\
		Hat man keine eigenen CVs mehr oder<br/>\n\
		erreicht der Opponent die vorgegebene Anzahl an Conquestpunkten oder<br/>\n\
		man gibt auf oder<br/>\n\
		das Zeitlimit endet und man hat weniger Conquestpunkte als der Opponent dann<br/>\n\
		wird dies als Niederlage gewertet.<br/>\n\
		</p>\n\
		<hr/>\n\
		<h3>Probleme</h3>\n\
		<p>\n\
		Kommt es aus technischen Gründen zu einem Spielabbruch, stehen den Teilnehmern folgende Optionen frei, ein Ergebnis zu ermitteln:<br/>\n\
		Einigung auf ein Ergebnis<br/>\n\
		Wiederholung des Spiels auf der selben Karte mit den selben Decks auf der selben Seite.<br/>\n\
		</p>\n\
		<hr/>\n\
		<h3>Ergebnis</h3>\n\
		<p>\n\
		Das Ergebnis ist nach dem Match unverzüglich einzutragen und ein Replay muss hochgeladen werden.<br/>\n\
		</p>\n\
		<hr/>\n\
		<h3>Spielername</h3>\n\
		<p>\n\
		Der Wargamename muss exakt mit dem Anmeldenamen übereinstimmen.<br/>\n\
		</p>\n\
	</body>\n\
</html>\n"
	return html

if __name__ == "__main__":
	app.config["SECRET_KEY"] = "BlaBlub42"
	#run_simple(host, port, app, use_reloader=True)
	CGIHandler().run(app)
	#WSGIServer(app).run()
