# -*- coding: utf-8 -*-

from datetime import date, timedelta
import logging
import os
import re
import threading
from time import localtime, strftime, mktime
import urllib2

from bs4 import BeautifulSoup

import markup
import retry_decorator


__author__ = "Aaron"
__version__ = 1.11
__modified__ = '4/3/15'

team_abbrvs = ['ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GS',
              'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NO', 'NY',
              'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SA', 'TOR', 'UTAH', 'WSH']

team_names = ['Hawks', 'Celtics', 'Nets', 'Hornets', 'Bulls', 'Cavaliers',
              'Mavericks', 'Nuggets', 'Pistons', 'Warriors', 'Rockets', 'Pacers',
              'Clippers', 'Lakers', 'Grizzlies', 'Heat', 'Bucks', 'Timberwolves',
              'Pelicans', 'Knicks', 'Thunder', 'Magic', '76ers', 'Suns',
              'Trail Blazers', 'Kings', 'Spurs', 'Raptors', 'Jazz', 'Wizards']

global total_games
total_games = 0

file_name = str(date.today()) + '.log'

script_dir = os.path.dirname(os.path.abspath(__file__))
dest_dir = os.path.join(script_dir, "logs")
   
try:
   os.makedirs(dest_dir)
except OSError:
   pass

path = os.path.join(dest_dir, file_name)

logging.basicConfig(filename=path,
                    format='(%(threadName)-10s) %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GameData(object):
   '''Class to represent a game played by a hockey team.

   :param link: html link to the game recap from ESPN.com
   :type link: string
   :param headline: the headline from the game recap
   :type headline: string
   :param date: the date the game was played
   :type date: string'''
   
   def __init__(self, link, headline, date):
      self.id = total_games
      self.link = link
      self.headline = headline
      self.date = date
      self.result = None
      
   def char_convert_link(self):
      '''Convert ampersands from the character '&' to the character encoding 
      '&amp;' to properly request html'''

      self.link = re.sub('[&]', '&amp;', self.link)
      
   def print_game_data(self):
      '''Print data of the class'''
      
      print self.id, self.headline, self.link, self.date, self.result
      
   def list_data(self):
      '''Return the data of the class as a list'''
      return [self.headline, self.link, self.date, self.result]
   
   def modify_headline(self):
      '''Change the headline to also include the game date and the result of
      the game'''
      
      headline = self.headline
      
      if self.date[4] == "0":
         self.headline = "[" + self.date[5:6] + "/" + self.date[6:] + "] "
      else:
         self.headline = "[" + self.date[4:6] + "/" + self.date[6:] + "] "
      try:
         self.headline = self.headline + self.result + " - " + headline
      except TypeError:
         logger.debug("TypeError from: " + self.link)
         try:
            self.headline = self.headline + self.result + " - No Headline"
         except TypeError:
            self.headline = self.headline + " - " + headline
         
   def find_winner(self, team_name, soup):
      '''Find the winner of the hockey game through the game recap.
   
      :param team_name: the name of the hockey team; used to check if this team
      was the winner
      :type team_name: string
      :param soup: the source file of the recap page
      :type soup: string'''
      
      matchup = soup.find(class_="matchup")
      home = matchup.find(class_="team home")
      home_team = str(home.find('a').text)
      home_score = int(home.find('span').text)
      away_score = int(matchup.find(class_="team away").find("span").text)
                     
      home = home_team == team_name
      
      if home_score > away_score and home:
         result = "W"
      elif home_score < away_score and home:
         result = "L"
      elif home_score > away_score:
         result = "L"
      elif home_score < away_score:
         result = "W"
      else:
         logger.debug("Error determining winner from: " + self.link)
         result = ""

      self.result = result
   
def page_response(link):
   '''Retrieve the source code of the page

   :param link: the link to the page that will be scraped
   :type link: string'''
   
   response = urlopen_with_retry(link)
   page_source = response.read()
   
   return BeautifulSoup(page_source)

def thread_jumpoff(team_ab, team_name):
   '''Intermediary function between the main function and the game extraction
   and xml generation

   :param team_ab: the team's abbreviated name
   :type team_ab: string
   :param team_name: the team's name
   :type team_name: string'''
   
   games = extract_game_data(team_ab, team_name)
   games.sort(key=lambda x: x.date, reverse=True)
     
   markup.xml_markup(games, team_ab, team_name)

   logger.info(strftime("%d-%b-%Y %H:%M:%S ", localtime()) + team_name + 
               " completed with " + str(len(games)) + " games logged")

def extract_game_data(team_ab, team_name):
   '''Extract the game data (date, headline, result) for each game the team 
   has played.

   :param team_ab: the team's abbreviated name
   :type team_ab: string
   :param team_name: the team's name
   :type team_name: string'''
   
   games = []
   link = "http://espn.go.com/nba/team/schedule/_/name/" + team_ab
   soup = page_response(link)
   global total_games
   
   for div in soup.find_all(attrs={"class" : "score"}):
      link_ending = str(div.find('a').get('href').encode('utf-8', 'ignore'))
      recap_link = "http://espn.go.com" + link_ending
#      print recap_link
      
      boxscore_link = "http://espn.go.com/nba/boxscore?gameId=" + recap_link[32:]

      recap_link_soup = page_response(recap_link)
      game_headline = get_game_headline(recap_link_soup, recap_link)
      
      boxscore_link_soup = page_response(boxscore_link)
      game_date = get_game_date(boxscore_link_soup)

      new_game = GameData(recap_link, game_headline, game_date)
      total_games += 1
      
      new_game.char_convert_link()
      new_game.find_winner(team_name, boxscore_link_soup)
      new_game.modify_headline()
      
#      new_game.print_game_data()

      games.append(new_game)
      
   return games

@retry_decorator.retry(urllib2.URLError, logger, tries=4, delay=3, backoff=2)
def urlopen_with_retry(link):
   return urllib2.urlopen(link)

def get_game_headline(soup, link):
   '''Extract the headline from the page source.

   :param soup: the source file of the recap page
   :type soup: string
   :param link: the link to the page that will was scraped; passed in case of 
   error for logging
   :type link: string'''
   
   try:
      for meta in soup.findAll('meta', {"property":'og:title'}):
         return meta.get('content')
   except urllib2.HTTPError:
      logger.debug('There was an error with the request from: ' + link)
      
def get_game_date(soup):
   '''Extract the headline from the page source.

   :param soup: the source file of the recap page
   :type soup: string'''
   
   for item in soup.find_all('a'):
      if '/nba/scoreboard?date=' in item.get('href'):
         return item.get('href')[21:]
      
def main():
   start_time = localtime()
   logger.info("Start time: " + strftime("%d-%b-%Y %H:%M:%S ", start_time))
   
   threads = []
   for team_ab, team_name in zip(team_abbrvs, team_names):
      t = threading.Thread(name="Thread-" + team_ab,
                           target=thread_jumpoff,
                           args=(team_ab, team_name))
      threads.append(t)

   # Start all threads
   [x.start() for x in threads]

   # Wait for all of them to finish
   [x.join() for x in threads]
   
   finish_time = localtime()
   logger.info("Finish time: " + strftime("%d-%b-%Y %H:%M:%S ", finish_time))
   logger.info("Total games: " + str(total_games))
   logger.info("Total time: " + 
               str(timedelta(seconds=mktime(finish_time) - mktime(start_time))))
   
if __name__ == '__main__':
   main()
