#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Exchange names for phones"""

# <https://github.com/uhhhuh/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import argparse
import logging
import csv
import sqlite3
from random import choice
from urllib.parse import quote
import requests
from lxml import etree


#logging config:
logger = logging.getLogger(__name__) #pylint: disable=invalid-name
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('namegetphone.log') #pylint: disable=invalid-name
ch = logging.StreamHandler() #pylint: disable=invalid-name
formatter_ch = logging.Formatter(fmt='[%(levelname)s] %(message)s') #pylint: disable=invalid-name
formatter_fh = logging.Formatter(fmt='[%(levelname)s] %(asctime)s %(message)s', datefmt='%H:%M:%S') #pylint: disable=invalid-name
ch.setFormatter(formatter_ch)
fh.setFormatter(formatter_fh)
ch.setLevel(logging.INFO)
fh.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.addHandler(fh)
#


# Ugly predefined
URL = 'http://nomerorg.biz/moskva/'
DB_FILENAME = 'database.db'
DB_SCHEME = 'scheme.sql'
with open('useragents.txt', 'rt') as ua_f:
    USERAGENTS = ua_f.read().splitlines()


def load_csv(csv_path):
    """Read csv into a list of {'idn': 'name'}"""
    with open(csv_path) as csvfile:
        reader = csv.DictReader(csvfile)
        personae = [{'id': row['id'], 'name': row['name']} for row in reader]
    logger.info('Loaded `%s`', csv_path)
    return personae


def build_form_data(lastname='', firstname='', middlename='', phone=''):
    """Prepare POST payload"""
    form_data = {
        'lastName':   lastname,
        'firstName':  firstname,
        'middleName': middlename,
        'phone':      phone,
        'searchButton': 'Найти',
        }
    return form_data


def get_page_text(page_url, form_data=None):
    """Retrieve webpage text, either with POST or with GET"""
    headers = {'User-Agent': choice(USERAGENTS)}
    logger.info('Fetching page...')
    if form_data is None:
        try:
            response = requests.get(page_url, headers)
        except Exception as err:
            logger.error('Error while GET. %s', err)
    else:
        try:
            response = requests.post(page_url, headers=headers, data=form_data)
        except Exception as err:
            logger.error('Error while POST. %s', err)
    return response.text


def get_page_tree(response_text):
    """Get lxml.etree"""
    try:
        tree = etree.HTML(response_text)
    except Exception as err:
        logger.error('Could\'t get page etree. %s', err)

    return tree


def parse_people(page_tree):
    """Find a table with people within the etree"""
    logger.info('Parsing page tree for people')
    parsed_people = []
    try:
        nodes = page_tree.xpath('//table[@class="w3-table w3-bordered w3-striped"]/tr')
    except Exception as err:
        logger.error("Couldn\'t parse people. %s", err)
    else:
        for num in range(1, len(nodes)):
            someone = {}
            name = nodes[num][0].text.title()
            phone = nodes[num][1].text
            birth = nodes[num][2].text
            street = nodes[num][3].text
            bld = nodes[num][4].text
            corp = nodes[num][5].text
            flat = nodes[num][6].text
            someone = {'name': name,
                       'phone': phone,
                       'birth': birth,
                       'street': street,
                       'building': bld,
                       'corpus': corp,
                       'flat': flat}
            if someone not in parsed_people:
                parsed_people.append(someone)
    return parsed_people


def build_next_page_href(page_number, last='', first='', middle='', phone=''):
    """Build a path to the next search results page"""
    if any([last, first, middle]) and not phone:
        logger.info('BUILDING NEXT_PAGE_URL for %s %s %s, PAGE # %s', last,
                    first, middle, page_number)
        next_page_href = quote('/moskva/lastName_'
                               + last + '_firstName_'
                               + first + '_middleName_'
                               + middle + '_pagenumber_'
                               + str(page_number)
                               + '.html')
    elif not any([last, first, middle]) and phone:
        # e.g `/moskva/phone_5636606_pagenumber_1.html`
        next_page_href = quote('/moskva/phone_'
                               + str(phone)
                               + '_pagenumber_'
                               + str(page_number)
                               + '.html')
    else:
        next_page_href = None
    return next_page_href


def build_next_page_url(page_number, last='', first='', middle='', phone=''):
    """Build a url for the next results page"""
    try:
        next_page_url = 'http://nomerorg.biz' + build_next_page_href(page_number,
                                                                     last,
                                                                     first,
                                                                     middle,
                                                                     phone)
    except Exception as err:
        logger.error('Unable to build next page url. %s', err)
        next_page_url = None
    return next_page_url


def any_more_people(page_tree, last, first, middle, page_number=1):
    """Check whether there's a path to the next page in etree"""
    next_page_href = build_next_page_href(page_number, last, first, middle)
    param = '//a/@href="' + next_page_href + '"'
    return bool(page_tree.xpath(param))


def any_more_phones(page_tree, phone, page_number=1):
    """Check whether there's a path to the next page in etree"""
    next_page_href = build_next_page_href(page_number, phone=phone)
    param = '//a/@href="' + next_page_href + '"'
    return bool(page_tree.xpath(param))


def unite_address_parts(*args):
    """Put together parts of the address: street, building, corpus, flat"""
    return ', '.join(filter(None, (args)))


def search_people(csv_personae):
    """Search people"""
    def extract_results(results):
        """Exctract the results of the parsed pages"""
        for result in results:
            if result['phone'] and result['phone'] not in person['phones']:
                person['phones'].append(result['phone'])
            if result['birth'] and result['birth'] not in person['birthdays']:
                person['birthdays'].append(result['birth'])
            addr = unite_address_parts(result['street'],
                                       result['building'],
                                       result['corpus'],
                                       result['flat'])
            if addr and addr not in person['addresses']:
                person['addresses'].append(addr)

    all_people = []
    for csv_person in csv_personae:
        persons_associated = []
        person = {'name': csv_person['name'],
                  'phones': [],
                  'birthdays': [],
                  'addresses': [],
                  'associated': persons_associated}

        last, first, middle = csv_person['name'].split()
        form_data = build_form_data(lastname=last, firstname=first, middlename=middle)
        response_text = get_page_text(URL, form_data)
        page_tree = get_page_tree(response_text)
        results = parse_people(page_tree) # people = [{}, {}, {}]
        extract_results(results)
        # check more people with the same name
        page_counter = 1
        while True:
            if any_more_people(page_tree, last, first, middle, page_counter):
                more_people_url = build_next_page_url(page_counter,
                                                      last=last,
                                                      first=first,
                                                      middle=middle)
                response_text = get_page_text(more_people_url)
                page_tree = get_page_tree(response_text)
                results = parse_people(page_tree) # people = [{}, {}, {}]
                extract_results(results)
                page_counter += 1
            else:
                break
        all_people.append(person)
    return all_people


def look_up(number):
    """Lookup phone numbers and get people"""
    found = []
    form_data = build_form_data(phone=number)
    response_text = get_page_text(URL, form_data)
    page_tree = get_page_tree(response_text)
    parsed_people = parse_people(page_tree) # people = [{}, {}, {}]
    """
    parsed_people = [{'name': 'Alice',
                      'phone': '111111',
                      'birth': '05.05.1950',
                      'street': 'Street1',
                      'building': '1',
                      'corpus': '4',
                      'flat': '44'},
                      {'name': 'Bob',
                      'phone': '222222',
                      'birth': '05.05.1980',
                      'street': 'Street2',
                      'building': '3',
                      'corpus': '4',
                      'flat': '55'}]"""
    for ppe in parsed_people:
        if (ppe['name'], ppe['birth']) not in [(i['name'], i['birth']) for i in found]:
            found.append({'name': ppe['name'], 'birth': ppe['birth']})
    page_counter = 1
    while True:
        if any_more_phones(page_tree, number, page_counter):
            more_phones_url = build_next_page_url(page_counter, phone=number)
            response_text = get_page_text(more_phones_url)
            page_tree = get_page_tree(response_text)
            parsed_people = parse_people(page_tree)
            for ppe in parsed_people:
                if (ppe['name'], ppe['birth']) not in [(i['name'], i['birth']) for i in found]:
                    found.append({'name': ppe['name'], 'birth': ppe['birth']})
            page_counter += 1
        else:
            break
    return found


def search_by_phone(number):
    """Search people by phone number"""
    logger.infot('LOOKING UP PHONE: %s', number)
    results = look_up(number)
    """
    results = [
        {'name': 'Alice', 'birth': '11.12.2001'},
        {'name': 'Bob', 'birth': '01.05.1999'},
        {'name':'Eve', 'birth':'04.02.1950'}]
    """
    return results


def save_to_sqlite(all_people):
    """Save people (list of dicts) to sqlite."""
    db_exists = os.path.exists(DB_FILENAME)
    with sqlite3.connect(DB_FILENAME) as dbase:
        if db_exists:
            logger.info('Database exists. Dropping old data')
            dbase.executescript("""
            DROP TABLE IF EXISTS person;
            DROP TABLE IF EXISTS phones;
            DROP TABLE IF EXISTS birthdays;
            DROP TABLE IF EXISTS addresses;
            DROP TABLE IF EXISTS persons_associated;
            """)
        else:
            logger.info('No database')
        with open(DB_SCHEME, 'rt') as fil:
            scheme = fil.read()
            logger.info('Creating tables')
            dbase.executescript(scheme)
        cur = dbase.cursor()
        #NB! ¿sql injection attack
        for person in all_people:
            cur.execute('INSERT INTO person VALUES (NULL, :name)', person)
            person_id = cur.lastrowid
            for phone in person['phones']:
                cur.execute('INSERT INTO phones VALUES (NULL, ?,?)', (person_id,
                                                                      phone))
            for bday in person['birthdays']:
                cur.execute('INSERT INTO birthdays VALUES (NULL, ?,?)', (person_id,
                                                                         bday))
            for addr in person['addresses']:
                cur.execute('INSERT INTO addresses VALUES (NULL, ?,?)', (person_id,
                                                                         addr))
            for ass in person['associated']:
                cur.execute('INSERT INTO persons_associated VALUES (NULL, ?,?,?)', (person_id,
                                                                                    ass['name'],
                                                                                    ass['birth']))

        cur.close()


if __name__ == '__main__':
    ARGP = argparse.ArgumentParser()
    """e.g. `namegetphone.py -i input.csv`  """
    ARGP.add_argument("-i", "--input_csv", help="CSV file containing people", type=str)
    ARGS = ARGP.parse_args()

    csv_data = load_csv(ARGS.input_csv)
    """
    csv_personae = [{'id': '123123123', 'name': 'Иванов Олег Петрович'},
                    {'id': '1231231', 'name': 'Иванов Фаина Венедиктовна'},
                    {'id': '123123124', 'name': 'Иванова Фаина Венедиктовна'}]
    """
    for p in csv_data:
        print(p['name'])

    all_searched_people = search_people(csv_data)

    for a_person in all_searched_people:
        for ph_number in a_person['phones']:
            ph_results = search_by_phone(ph_number)
            #ph_results = [{'name':'Alice', 'birth': '77.77.7777'},
            #              {'name':'Bob', 'birth': '88.88.8888'}]
            for phr in ph_results:
                # exclude dupes
                if (phr['name'], phr['birth']) not in [(i['name'], i['birth']) for i in a_person['associated']]:
                    a_person['associated'].append(phr)
    save_to_sqlite(all_searched_people)
