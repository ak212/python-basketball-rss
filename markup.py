'''
Created on Oct 6, 2014

@author: Aaron
'''
import os
 
def xml_markup(games, team_ab, team_name):
   file_name = team_ab + "_feed.xml"
   
   #Used code from http://stackoverflow.com/questions/7935972/writing-to-a-new-directory-in-python-without-changing-directory
   
   script_dir = os.path.dirname(os.path.abspath(__file__))
   dest_dir = os.path.join(script_dir, "feeds", team_ab)
   
   try:
      os.makedirs(dest_dir)
   except OSError:
      pass # already exists\\

   path = os.path.join(dest_dir, file_name)
   
   with open(path, 'w') as xml:
      xml.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
      xml.write("<rss version='2.0'>\n")
      xml.write("<channel>\n")
      xml.write("<title>%s scores</title>\n" % team_name)
      xml.write("<description>Latest %s scores</description>\n" % team_name)
      xml.write("<link>http://espn.go.com/nhl/team/schedule/_/name/%s</link>\n" % team_ab)
   
      for game in games:
         xml.write("<item>\n")
         xml.write("<title>%s</title>\n" % game.headline)
         xml.write("<link>%s</link>\n" % game.link)
         xml.write("</item>\n")
      xml.write("</channel>\n</rss>")
   xml.close()
