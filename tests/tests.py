#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import namegetphone
import pickle
from lxml import etree

class TestHell(unittest.TestCase):

    

    def setUp(self):
        self.URL = 'http://nomerorg.biz/moskva/'
        self.DB_FILENAME = 'database.db'
        self.DB_SCHEME = 'scheme.sql'
        with open('useragents.txt', 'rt') as ua_f:
            self.USERAGENTS = ua_f.read().splitlines()
        self.csv_filename = 'tests/personae.csv'
        self.csv_personae = [{'id': '40203e8c-1d8a-4428-beff-71c3d0fc211b',
                     'name': 'Абрамов Иван Николаевич'},
                    {'id': '7f582309-4d2b-4225-b0f6-107e754a3d3f',
                      'name': 'Авдеев Александр Александрович'},
                    {'id': 'f4ecde21-be1e-4de7-9604-eaf831e6556b',
                     'name': 'Агаев Ваха Абуевич'},
                    {'id': 'cd4b360d-8cf6-46d5-825f-ba2139459c35',
                     'name': 'Адучиев Батор Канурович'},
                    {'id': 'df90b0f7-96c9-4737-9a43-d3ed433f2898',
                     'name': 'Неверов Сергей Иванович'}]



    def tearDown(self):
        pass

    
    def test_load_csv(self):
        self.csv = namegetphone.load_csv(self.csv_filename)
        self.assertEqual(self.csv_personae, self.csv)

        
    def test_build_form_data(self):
        form1 = {'firstName': 'FIRST',
                 'lastName': 'LAST',
                 'middleName': 'MIDDLE',
                 'phone': '',
                 'searchButton': 'Найти'}

        form2 = {'firstName': 'FIRST',
                 'lastName': 'LAST',
                 'middleName': 'MIDDLE',
                 'phone': '',
                 'searchButton': 'Найти'}
        form3 = {'firstName': '',
                 'lastName': '',
                 'middleName': '',
                 'phone': '1111-1111',
                 'searchButton': 'Найти'}
        self.f1 = namegetphone.build_form_data(lastname='LAST', firstname='FIRST', middlename='MIDDLE')
        self.f2 = namegetphone.build_form_data(middlename='MIDDLE', lastname='LAST', firstname='FIRST')
        self.f3 = namegetphone.build_form_data(phone='1111-1111')

        self.assertEqual(form1, self.f1)
        self.assertEqual(form2, self.f2)
        self.assertEqual(form3, self.f3)

                                                                     
    def test_get_page_tree(self):
        with open('tests/response_text.pkl', 'rb') as pkl:
            self.response_text = pickle.load(pkl)

        self.page_tree = namegetphone.get_page_tree(self.response_text)
        self.assertTrue(isinstance(self.page_tree, etree._Element))

        
    def test_parse_people(self):
        with open('tests/parsed_people.pkl', 'rb') as pkl:
            self.parsed_people = pickle.load(pkl)

        with open('tests/response_text.pkl', 'rb') as pkl:
            self.response_text = pickle.load(pkl)

        self.ptree = namegetphone.get_page_tree(self.response_text)
        self.same_people = namegetphone.parse_people(self.ptree)
        self.assertEqual(self.parsed_people, self.same_people)


    def test_build_next_page_href(self):
        self.href1 = '/moskva/lastName_LAST_firstName_FIRST_middleName_MIDDLE_pagenumber_1.html'
        self.href1_ = namegetphone.build_next_page_href(1, last='LAST', middle='MIDDLE', first='FIRST')
        
        self.href2 = namegetphone.build_next_page_href(1, phone='222333')
        self.href2_ = '/moskva/phone_222333_pagenumber_1.html'

        self.href3 = namegetphone.build_next_page_href(1, phone='222333', last='LAST')
        self.href3_ = None
        
        self.assertEqual(self.href1, self.href1_)
        self.assertEqual(self.href2, self.href2_)
        self.assertFalse(self.href3)


    def test_build_next_page_url(self):
        self.next_url = namegetphone.build_next_page_url(1, last='LAST', middle='MIDDLE', first='FIRST')
        self.assertEqual(self.next_url, 'http://nomerorg.biz/moskva/lastName_LAST_firstName_FIRST_middleName_MIDDLE_pagenumber_1.html')
        self.assertFalse(namegetphone.build_next_page_url(1, last='LAST', middle='MIDDLE', first='FIRST', phone='555-555'))
        self.assertEqual(namegetphone.build_next_page_url(1, phone='555555'), 'http://nomerorg.biz/moskva/phone_555555_pagenumber_1.html')


    def test_unite_address_parts(self):
        self.assertEqual(namegetphone.unite_address_parts('Street One', 'Corp 1', 'Building 2', 'Flat 4'), 'Street One, Corp 1, Building 2, Flat 4')
