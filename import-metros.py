#!/usr/bin/env python
import re
import os
import sys
import urllib2

from os import unlink
from json import loads, dumps
from glob import glob
from shutil import rmtree
from os.path import join, isdir, expanduser, exists
from collections import defaultdict
from BeautifulSoup import BeautifulSoup
from subprocess import call

if not exists('./configure.py'):
  sys.stderr.write('Error: configure.py does not exist, did you forget to create it from the sample (configure.py.sample)?\n')
  sys.exit(1)
elif exists('./configure.pyc'):
  unlink('./configure.pyc')

from configure import config
from lib.utils import copy_tree

def main():
  print_metro_list()
  map_id = raw_input("Metro ID: ")
  osm_filename = get_metro_list_by_id( map_id )

  print 'Downloading:  ' + osm_filename
  download_map(osm_filename)

  if database_exists(config["postgis"]["dbname"]) == 0:
    create_postgis_database(postgis_database)

  import_osm(osm_filename)


def database_exists( dbname ):
  cmd='psql -t -c "SELECT COUNT(*) FROM pg_catalog.pg_database WHERE datname = \''+dbname+'\'"  '
  # print cmd
  response = os.popen(cmd,"r")
  return int(response.readline())
  

def create_postgis_database( dbname ):
  # createdb -T template_postgis my_spatial_db
  cmd='psql -t -c "CREATE DATABASE '+dbname+' TEMPLATE template_postgis"'
  print cmd
  response = os.popen(cmd,"r")


def import_osm( osm_filename  ):
  database_name = ''
  database_username = ''
  if len(config["postgis"]["dbname"]) > 0:
    database_name = " -d " + config["postgis"]["dbname"] 

  if len(config["postgis"]["user"]) > 0:
    database_username = " -U " + config["postgis"]["user"] 

  cmd = "imposm " + database_name + database_username + "  -m ./imposm-mapping.py --read --write --optimize --deploy-production-tables --overwrite-cache  " + metro_name_to_local_path(osm_filename)
  print cmd
  call(cmd, shell=True)


def get_metro_list():
  soup = BeautifulSoup(download_html('http://metro.teczno.com/'))
  cities = soup.findAll('li', {'class': 'link'})
  return cities

def print_metro_list():
  cities = get_metro_list()
  for i,city in enumerate(cities):
    print "%d => %s"%(i,city.text)    

def get_metro_list_by_id(city_id):
  cities = get_metro_list()
  print city_id
  for i,city in enumerate(cities):
    if int(i) == int(city_id):
      return city.text



def metro_name_to_local_filename(filename):
  return filename.lower().replace(' ', '-').replace('.osm.bz2', '') + '.osm.bz2'


def metro_name_to_local_path(filename):
  return './pbf/'+ metro_name_to_local_filename(filename)

def download_map(filename):
  url = "http://osm-metro-extracts.s3.amazonaws.com/" + metro_name_to_local_filename(filename)
  print url
  download_file( url )



def download_file(url):
  filename = os.path.basename(url)
  downloaded = urllib2.urlopen(url)
  output = open(metro_name_to_local_path(filename),'wb')
  output.write(downloaded.read())
  output.close()

def download_html(url):
  response = urllib2.urlopen(url)
  headers = response.info()
  data = response.read()
  return data

main()
