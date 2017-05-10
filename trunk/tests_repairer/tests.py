# -*- coding: utf-8 -*-

import unittest
import os
from cache_repairer.database_manager import DatabaseManager
from cache_repairer.utils import get_remove_date, get_dir_xml


class TestDbManager(unittest.TestCase):

    def setUp(self):
        path = os.path.dirname(os.path.realpath(__file__)) + '/test_db.sqlite'
        self.cache_pathes = ['/some/dir/path', '/some/dir/path', '/another/dir/path',
                             '/dir1/dir2/dir3', '/last/dir/name']
        self.db = DatabaseManager(path)
        for path in self.cache_pathes:
            self.db.add(path)

    def test_add(self):
        self.db.add('/new/path/value')
        self.assertEqual(len(self.db.select_all_data()), len(self.cache_pathes))

    def test_select_last(self):
        last_id = self.db.select_last()[0]
        self.assertEqual(last_id, len(self.cache_pathes)-1)

    def test_select(self):
        selected = self.db.select(len(self.cache_pathes)-1)[1]
        last = self.db.select_last()[1]
        self.assertEqual(last, selected)

    def test_select_all(self):
        all = self.db.select_all_data()
        self.assertEqual(len(all), len(self.cache_pathes)-1)

    def test_delete_last(self):
        last_before = self.db.select_last()[0]
        self.db.delete_last()
        last_after = self.db.select_last()[0]
        self.assertEqual(last_before, last_after+1)

    def test_delete_all(self):
        self.db.delete_all_data()
        all = self.db.select_all_data()
        self.assertEqual(len(all), 0)

    def tearDown(self):
        del self.db


class TestUtils(unittest.TestCase):

    def test_get_remove_date(self):
        path = os.path.realpath(__file__)
        date = get_remove_date(path, 365)
        from datetime import datetime
        now_year = int(datetime.now().strftime("%Y"))+1
        self.assertTrue(str(now_year) in date)

if __name__ == "__main__":
    unittest.main()
