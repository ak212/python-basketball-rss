# -*- coding: utf-8 -*-

'''
Created on Oct 6, 2014

@author: Aaron
'''
import urllib2
from bs4 import BeautifulSoup
import re
import os
import logging
import threading
from datetime import date, timedelta
from time import localtime, strftime, mktime
 
import markup
import retry_decorator

team_abbrvs = ['ATL','BOS','BKN','CHA','CHI','CLE','DAL','DEN','DET','GS',
              'HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NO','NY', 
              'OKC','ORL','PHI','PHX','POR','SAC','SA','TOR','UTAH','WSH']

team_names = ['Hawks','Celtics','Nets','Hornets','Bulls','Cavaliers', 
              'Mavericks','Nuggets','Pistons','Warriors','Rockets','Pacers', 
              'Clippers','Lakers','Grizzlies','Heat','Bucks','Timberwolves', 
              'Pelicans','Knicks','Thunder','Magic','76ers','Suns', 
              'Trail Blazers','Kings','Spurs','Raptors','Jazz','Wizards']

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
   def __init__(self, link, headline, date):
      self.link = link
      self.headline = headline
      self.date = date
      self.result = None
      
   def char_convert_link(self):
      self.link = re.sub('[&]', '&amp;', self.link)
      
   def print_game_data(self):
      print self.headline, self.link, self.date, self.result
      
   def list_data(self):
      return [self.headline, self.link, self.date, self.result]
   
   def modify_headline(self, link):
      headline = self.headline
      
      if self.date[4] == "0":
         self.headline = "[" + self.date[5:6] + "/" + self.date[6:] + "] "
      else:
         self.headline = "[" + self.date[4:6] + "/" + self.date[6:] + "] "
      try:
         self.headline = self.headline + self.result + " - " + headline
      except TypeError:
         logger.debug("TypeError from: " + link)
         self.headline = self.headline + self.result + " No Headline"
         
   def find_winner(self, team_name, soup, link):
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
         logger.debug("Error determining winner from: " + link)
         result = ""

      self.result = result
   
def page_response(link):
   response = urlopen_with_retry(link)
   page_source = response.read()
   
   return BeautifulSoup(page_source)

def thread_jumpoff(team_ab, team_name):
   games = extract_game_data(team_ab, team_name)
   games.sort(key=lambda x: x.date, reverse=True)
     
   markup.xml_markup(games, team_ab, team_name)

   logger.info(strftime("%d-%b-%Y %H:%M:%S ", localtime()) + team_name + 
               " completed with " + str(len(games)) + " games logged")

def extract_game_data(team_ab, team_name):
   games = []
   link = "http://espn.go.com/nba/team/schedule/_/name/" + team_ab
   soup = page_response(link)
   
   for div in soup.find_all(attrs={"class" : "score"}):
      link_ending = str(div.find('a').get('href').encode('utf-8', 'ignore'))
      complete_link = "http://espn.go.com" + link_ending

      complete_link_soup = page_response(complete_link)
      game_headline = get_game_headline(complete_link_soup, complete_link)
      game_date = get_game_date(complete_link_soup)

      new_game = GameData(complete_link, game_headline, game_date)
      
      new_game.char_convert_link()
      new_game.find_winner(team_name, complete_link_soup, complete_link)
      new_game.modify_headline(complete_link)
      
      games.append(new_game)
      
   return games

@retry_decorator.retry(urllib2.URLError, logger, tries=4, delay=3, backoff=2)
def urlopen_with_retry(link):
   return urllib2.urlopen(link)

def get_game_headline(soup, link):
   try:
      for meta in soup.findAll('meta', {"property":'og:title'}):
         return meta.get('content')
   except urllib2.HTTPError:
      logger.debug('There was an error with the request from: ' + link)
      
def get_game_date(soup):
   scoreboard = soup.find(class_="scoreboard-strip-wrapper").find('a')
   date_string = str(scoreboard.get('href').encode('utf-8', 'ignore'))

   return date_string[21:]
      
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
   logger.info("Total time: " + 
               str(timedelta(seconds=mktime(finish_time)-mktime(start_time))))
   
if __name__ == '__main__':
   main()
