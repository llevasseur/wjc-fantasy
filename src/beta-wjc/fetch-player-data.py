from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import requests
from bs4 import BeautifulSoup
import re
import json
import os

cwd = os.getcwd()


def getSoup(url):
  response = requests.get(url)
  html = response.content
  
  return BeautifulSoup(html, 'html.parser')

def handleTd(obj, td):
  cl = td.get('class')

  ## Parse Name, href, and Position
  if cl == ['player']:
    a_list = td.find_all('a')
    for a in a_list:
      match = re.match('(.*)\s\((.*)\)', a.text)
      if match:
        name, pos = match.groups()
        if pos != "D": pos = 'F'
        obj["name"] = name
        obj["pos"] = pos
      elif a.text != "\n\n":
        obj["name"] = a.text
        obj["pos"] = "G"
        # Account for goalies getting points and penalties
        obj["g"], obj["a"], obj["pim"] = "0", "0", "0" 
      else: continue
      obj["href"] = a.get('href')

  ## Parse Team
  elif cl == ['team']:
    # if "name" in obj.keys(): print(f"Parsing team for {obj['name']}")
    a_list = td.find_all('a')
    for a in a_list:
      match = re.match('(.*) U20', a.text)
      if match:
        obj["team"] = match.group(1)
        # print(f"\t Found {match.group(1)}")

  # Parse Stats
  elif cl in [['g'], ['a'], ['pim'], ['pm'], ['gaa']]:
    obj[cl[0]] = td.text.strip()

  elif cl and 'svp' in cl:
    obj['svp'] = td.text.strip()


def getInnerWrapper(soup):
  div_list = soup.find_all('div')
  for div in div_list:
    if div.get("class") == ['innerwrapper']:
      return div

def getPlayersFromSoup(players, soup):
  inner_wrapper = getInnerWrapper(soup)
  if inner_wrapper:
    tr_list = inner_wrapper.find_all('tr')
  else:
    print("### INNER WRAPPER NOT FOUND")
    return

  for tr in tr_list:
    td_list = tr.find_all('td')

    player_obj = {}

    for td in td_list:
      handleTd(player_obj, td)
      
    if player_obj and "name" in player_obj.keys():
        players[player_obj["name"]] = player_obj

def main():
  players = {}
  
  for i in range(1, 5):
    print(f"Processing skater webpage {i}...")
    soup = getSoup("https://www.eliteprospects.com/league/wjc-20/stats/2023-2024?page="+str(i))

    getPlayersFromSoup(players, soup)

  print(f"Done!")
  
  with open(cwd + '/json/beta-wjc/2023-24/ep-player-data.json', 'w') as json_file:
    json_file.write(json.dumps(players, indent=4))

    print(f'''
    Player data has been fetched from https://www.eliteprospects.com and written to /json/beta-wjc/2023-24/ep-player-data.json
    Run `python src/beta-wjc/write-manual-data.py` to add SOG and TPM to the data in /json/beta-wjc/2023-24/manual-player-data.json
    ''')

if __name__ == "__main__":
  main()