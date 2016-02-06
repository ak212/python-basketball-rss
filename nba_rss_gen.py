# -*- coding: utf-8 -*-

from datetime import date, timedelta, datetime
import logging
import os
import re
import sys
import threading
from time import localtime, strftime, mktime
import urllib2

from bs4 import BeautifulSoup
import pymysql

import GameData
import log
import markup
import retry_decorator


__author__ = "Aaron"
__version__ = 2.1
__modified__ = '2/5/2016'

team_abbrvs = ['ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GS',
              'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NO', 'NY',
              'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SA', 'TOR', 'UTA', 'WSH']

team_names = ['Hawks', 'Celtics', 'Nets', 'Hornets', 'Bulls', 'Cavaliers',
              'Mavericks', 'Nuggets', 'Pistons', 'Warriors', 'Rockets', 'Pacers',
              'Clippers', 'Lakers', 'Grizzlies', 'Heat', 'Bucks', 'Timberwolves',
              'Pelicans', 'Knicks', 'Thunder', 'Magic', '76ers', 'Suns',
              'Trail Blazers', 'Kings', 'Spurs', 'Raptors', 'Jazz', 'Wizards']

logger = log.setup_custom_logger('root')
dbLastDate = None
totalGames = None

file_name = str(date.today()) + '.log'

def initDB():
   return pymysql.connect(host='localhost', port=3306, user='root', passwd=sys.argv[1], db='NBA')

def insertGame(gameData, teamAb, teamName):
   connection = initDB()
   
   try:
      with connection.cursor() as cursor:
         sql = "INSERT INTO `GameData` VALUES (%s, %s, %s, %s, %s, %s, %s)"
         cursor.execute(sql, (gameData.id, gameData.link, gameData.headline,
                              gameData.date, gameData.result, teamAb, teamName))

      connection.commit()

   finally:
      connection.close()

def retrieveGames(teamAb):
   connection = initDB()
   result = None
   games = []
   
   try:
      with connection.cursor() as cursor:
         sql = "SELECT * FROM `GameData` WHERE `team_ab`=%s"
         cursor.execute(sql, (teamAb))
         result = cursor.fetchall()

   finally:
      connection.close()
    
   for game in result:
      games.append(GameData.GameData(game[0], game[1], game[2], game[3], game[4]))

   return games

def getTotalGames():
   global totalGames
   connection = initDB()
   result = None
   
   try:
      with connection.cursor() as cursor:
         sql = "SELECT max(id) FROM `GameData`"
         cursor.execute(sql)
         result = cursor.fetchone()

   finally:
      connection.close()
   
   if result[0] != None:
      totalGames = int(result[0]) + 1
   else:
      totalGames = 0

def getLastDate():
   global dbLastDate
   global totalGames
   
   connection = initDB()
   daysAgo = 365
   
   try:
      with connection.cursor() as cursor:
         sql = "SELECT game_date FROM `GameData` WHERE `id`=%s"
         cursor.execute(sql, (str(totalGames)))
         result = cursor.fetchone()
         
         currentDate = date.today()
       
         if result != None:
            for dateDB in result:
               # whatever the date string is
               formatDate = datetime.strptime(dateDB, "%Y%m%d").date()
               
               daysAgo = min((currentDate - formatDate).days, daysAgo)

   finally:
      connection.close()
    
    
   dbLastDate = currentDate - timedelta(days=daysAgo)

def pageResponse(link):
   '''Retrieve the source code of the page

   :param link: the link to the page that will be scraped
   :type link: string'''
   
   response = urlopen_with_retry(link)
   page_source = response.read()
   
   return BeautifulSoup(page_source)

def teamExtractAndMarkup(team_ab, team_name):
   '''Intermediary function between the main function and the game extraction
   and xml generation

   :param team_ab: the team's abbreviated name
   :type team_ab: string
   :param team_name: the team's name
   :type team_name: string'''
   
   games = extractGameData(team_ab, team_name)
   games.sort(key=lambda x: x.date, reverse=True)
     
   markup.xml_markup(games, team_ab, team_name)

   logger.info(strftime("%d-%b-%Y %H:%M:%S ", localtime()) + team_name + 
               " completed with " + str(len(games)) + " games logged")

def extractGameData(teamAb, teamName):
   '''Extract the game data (date, headline, result) for each game the team 
   has played.

   :param team_ab: the team's abbreviated name
   :type team_ab: string
   :param team_name: the team's name
   :type team_name: string'''
   
   global totalGames
   global logger
   
   games = retrieveGames(teamAb)
   links = [game.link for game in games]
   schedLink = "http://espn.go.com/nba/team/schedule/_/name/" + teamAb
   soup = pageResponse(schedLink)
   
   for div in soup.find_all(attrs={"class" : "score"}):
      recapLinkEnding = str(div.find('a').get('href').encode('utf-8', 'ignore'))
      if "recap" in recapLinkEnding:
         recapLink = "http://espn.go.com" + recapLinkEnding
         
         if recapLink not in links:
            boxscoreLink = "http://espn.go.com/nba/boxscore?gameId=" + recapLink[32:]
            
            recapLinkSoup = pageResponse(recapLink)
            gameHeadline = getGameHeadline(recapLinkSoup, recapLink)
            gameDate = getGameDate(recapLinkSoup, recapLink)
      
            if gameDate == "PRE":
               formattedDate = datetime.strptime("20150901", "%Y%m%d").date()
            elif gameDate != None:
               formattedDate = datetime.strptime(gameDate, "%Y%m%d").date()
            else:
               formattedDate = datetime.strptime("20150901", "%Y%m%d").date()
             
            formattedDate = formattedDate - timedelta(days=1)
             
            if (formattedDate - dbLastDate).days > 0:
               newGame = GameData.GameData(totalGames, recapLink, gameHeadline, re.sub('-', '', str(formattedDate)))
         
               totalGames += 1
               
               newGame.charConvertLink()
               boxscoreLinkSoup = pageResponse(boxscoreLink)
               newGame.findWinner(teamName, boxscoreLink, boxscoreLinkSoup)
               newGame.modifyHeadline()
               #      newGame.print_game_data()
               insertGame(newGame, teamAb, teamName)
               games.append(newGame)

         else:
            logger.debug("Already have game with link " + recapLink)
      
   return games


@retry_decorator.retry(urllib2.URLError, logger, tries=4, delay=3, backoff=2)
def urlopen_with_retry(link):
   return urllib2.urlopen(link)

def getGameHeadline(soup, link):
   '''Extract the headline from the page source.

   :param soup: the source file of the recap page
   :type soup: string
   :param link: the link to the page that will was scraped; passed in case of 
   error for logging
   :type link: string'''
   
   try:
      return soup.title.string
   except urllib2.HTTPError:
      logger.debug('There was an error with the request from: ' + link)
      
def getGameDate(soup, link):
   '''Extract the headline from the page source.

   :param soup: the source file of the recap page
   :type soup: string'''
   
   try:
      if "boxscore" in link:
         return "PRE"
      else:
         base = soup.findAll('meta', {"name":'DC.date.issued'})
         date = base[0]['content'].encode('utf-8')[:10]
         return re.sub('-', '', date)
   except urllib2.HTTPError:
      logger.debug('There was an error with the request from: ' + link)
   except IndexError:
      logger.debug('Could not extract date from: ' + str(base))
      
def main():
   global totalGames
   getTotalGames()
   dbLastDate = getLastDate()
   
   startTime = localtime()
   logger.info("Start time: " + strftime("%d-%b-%Y %H:%M:%S ", startTime))
   
   threads = []
   for teamAb, teamName in zip(team_abbrvs, team_names):
      t = threading.Thread(name="Thread-" + teamAb,
                           target=teamExtractAndMarkup,
                           args=(teamAb, teamName))
      threads.append(t)

   # Start all threads
   [thread.start() for thread in threads]

   # Wait for all of them to finish
   [thread.join() for thread in threads]
   
   getTotalGames()
   finish_time = localtime()
   logger.info("Finish time: " + strftime("%d-%b-%Y %H:%M:%S ", finish_time))
   logger.info("Total games: " + str(totalGames))
   logger.info("Total time: " + 
               str(timedelta(seconds=mktime(finish_time) - mktime(startTime))))
   
if __name__ == '__main__':
   main()
