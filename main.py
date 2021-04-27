#!/usr/bin/env python3

import sys
import os
import getopt
import re
import requests
import traceback
from bs4 import BeautifulSoup

def usage():
	print('Usage: ' + sys.argv[0] + ' -p package_name')
	print('You can also add -v for verbose mode')
	print('This program respects the USE environment variable')
	print('Either USE, or -p, or both must be given')
	return -1

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
			possible_overlay = mess.attrs['id']
			if possible_overlay not in self.overlays:
				if verbose == True: print('Adding overlay: ' + possible_overlay)
				self.overlays.append(possible_overlay)

class zugaina_results(object):
	def __extract_page_count(self):
		self.soup = BeautifulSoup(self.response.text, "html.parser")
		top = 1
		for item in self.soup.find('div', attrs={'class': 'pager'}).findChildren('a'):
			if item.text.isnumeric():
				top = int(item.text)
		return top

	def __init__(self, package_name, useflags, verbose, debug=False):
		self.base_url = 'http://gpo.zugaina.org/Search?search=' + package_name + '&use=' + useflags
		self.verbose = verbose
		self.session = requests
		self.response = self.session.get(self.base_url)
		self.page_count = self.__extract_page_count()
		self.current_page = 1
		self.packages = []
		if debug == False:
			self.get_packages_from_current_page()
			self.get_packages_from_remaining_pages()
			self.list_packages()

	def get_next_page(self):
		if self.current_page != self.page_count:
			self.current_page += 1
			url = self.base_url + '&page=' + str(self.current_page)
			self.response = self.session.get(url)
			self.soup = BeautifulSoup(self.response.text, "html.parser")
			if self.verbose == True: print('Fetching page number ' + str(self.current_page))

	def get_packages_from_current_page(self):
		for item in self.soup.find('div', attrs={'id': 'search_results'}).findAll('a'):
			self.packages.append(package_object(item, self.verbose))

	def list_packages(self):
		if self.verbose == True: print("")
		for item in self.packages:
			print(item.package_name + ': ' + item.description)
			for overlay in item.overlays:
				print("\t" + overlay)
			print("")

	def get_packages_from_remaining_pages(self):
		while self.current_page < self.page_count:
			self.get_next_page()
			self.get_packages_from_current_page()

def main():
	package = ""
	verbose = False
	useflags = re.sub(" ", "+", os.environ.get('USE', ''))
	try:
		opts, argv = getopt.getopt(sys.argv[1:], 'p:v')
	except getopt.GetoptError:
		traceback.print_exc()
		print("")
		return usage()
	for key, value in opts:
		if key == '-p':
			package = value
		if key == '-v':
			verbose = True
	if package == "" and useflags == "":
		return usage()
	zugaina_results(package, useflags, verbose)
	return 0

if __name__ == '__main__':
	result = main()
	sys.exit(result)
