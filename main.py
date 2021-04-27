#!/usr/bin/env python3

import sys
import os
import getopt
import re
import requests
import pdb
import traceback
from bs4 import BeautifulSoup

def usage():
	print('Usage: ' + sys.argv[0] + ' -p package_name')
	print('You can also add -v for verbose mode')
	print('This program respects the USE environment variable')
	return -1

def extract_page_count(soup):
	top = 1
	for item in soup.find('div', attrs={'class': 'pager'}).findChildren('a'):
		try:
			top = int(item.text)
		except ValueError:
			pass
	return top

class package_object(object):
	def __init__(self, item, verbose):
		self.package_name = re.sub("^/", "", item.attrs['href'])
		self.description = re.sub("^"+ self.package_name + " ", "", item.find('div').text)
		if verbose == True: print('Found package: ' + self.package_name)
		url = 'http://gpo.zugaina.org/' + self.package_name
		session = requests
		response = session.get(url)
		soup = BeautifulSoup(response.text, "html.parser")
		self.overlays = []
		for mess in soup.find('div', attrs={'id': 'ebuild_list'}).find('ul').findAll('div', attrs={'id': re.compile('.*')}):
			possible_overlay = re.sub("^Overlay: ", "", mess.find('li').find('div', attrs={'style': 'font-size:1.5em;margin-left:40em;'}).text)
			if possible_overlay not in self.overlays:
				if verbose == True: print('Adding overlay: ' + possible_overlay)
				self.overlays.append(possible_overlay)

def display_results(package, useflags, verbose):
	url = 'http://gpo.zugaina.org/Search?search=' + package + '&use=' + useflags
	session = requests
	response = session.get(url)
	soup = BeautifulSoup(response.text, "html.parser")
	count = 0
	page_count = extract_page_count(soup)
	packages = []
	while count < page_count:
		for item in soup.find('div', attrs={'id': 'search_results'}).findAll('a'):
			packages.append(package_object(item, verbose))
		new_url = url + '&page=' + str(count)
		response = session.get(new_url)
		soup = BeautifulSoup(response.text, "html.parser")
		count += 1
	if verbose == True: print("")
	for item in packages:
		print(item.package_name + ': ' + item.description)
		for overlay in item.overlays:
			print("\t" + overlay)
		print("")
	return 0

def main():
	package = ""
	verbose = False
	try:
		useflags = re.sub(" ", "+", os.environ['USE'])
	except KeyError:
		useflags = ""
	try:
		opts, argv = getopt.getopt(sys.argv[1:], 'p:v')
	except getopt.GetoptError:
		traceback.print_exc()
		print("")
		return usage()
	for k, v in opts:
		if k == '-p':
			package = v
		if k == '-v':
			verbose = True
	if package == "":
		return usage()
	return display_results(package, useflags, verbose)

if __name__ == '__main__':
	result = main()
	sys.exit(result)
