'''
Created on Jan 23, 2016

@author: Aaron
'''

from datetime import date
import logging
import os


def setup_custom_logger(name):
   logging.basicConfig(filename=getFilePath(),
                    format='(%(threadName)-10s) %(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
                    level=logging.DEBUG)
   logger = logging.getLogger(name)
   if not len(logger.handlers):
      logger = logging.getLogger(name)
   
   return logger

def getFilePath():
   fileName = str(date.today()) + '.log'
   
   scriptDir = os.path.dirname(os.path.abspath(__file__))
   destDir = os.path.join(scriptDir, "logs")
      
   try:
      os.makedirs(destDir)
   except OSError:
      pass
   
   return os.path.join(destDir, fileName)