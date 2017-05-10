# -*- coding: utf-8 -*-

import os
import json
import requests
from job_launcher.abstract_job import AbstractJob
from abc import ABCMeta

from job_launcher.utils import auth_web, get_data_from_web, create_data_on_web, update_data_on_web
from job_launcher.exceptions import *
from cache_repairer.utils import get_dir_xml, get_remove_date
from cache_repairer.exceptions import *


class RepairerJob(AbstractJob, metaclass=ABCMeta):
    """
        Добавляет отсутствующие в хранилище кэша записи из файловой системы

        Получает через запрос к API базовый путь, где хранится кэш.
        Выполняет листинг директорий в файловой системе по базовому пути.
        Записывает в локальную БД результаты листинга.
        Берет по одной записи из базы и делает запрос к API по наличию пути в хранилище.
        Если путь отсутствует, создает новую запись в хранилище.
        Если путь есть, но отсутствует region_id, обновляет запись и пытается пересчитать region_id.
    """
    def __init__(self, params=None):
        super().__init__()
        if params:
            self.type = params['type']

            if self.type == 'delivery':
                self.value = 'delivery_cache'
                self.segm = 4

            self.host = params['data_host']
            self.data_uri = params['data_uri']
            self.depth = params['depth']
            self.days = params['store_days']
            self.auth_url = params['auth_url']
            self.username = params['username']
            self.password = params['password']
            self.cook = self.get_cook()
            self.base_path = self.get_storage_path()
        else:
            raise JobError('Получен пустой словарь с настройками')

    def get_cook(self):
        try:
            cook = auth_web(self.auth_url, self.username, self.password)
        except Exception as ex:
            raise CacheRepairerError('Ошибка при получении куки-файла: {}'.format(ex))
        return cook

    def get_storage_path(self):
        """
            Получает файловый путь хранилища кэша через запрос к API

        :return:        путь в текстовом формате
        """
        try:
            value, path = None, None
            data_uri = os.path.join(self.host, 'settings/paths?type={}'.format(self.value))
            resp = requests.get(data_uri, cookies=self.cook)
            if resp.status_code == 200:
                path = json.loads(resp.text)['data']['local']
        except Exception as ex:
            raise CacheRepairerError('Ошибка при получении пути к хранилищу: {}'.format(ex))
        return path

    @staticmethod
    def inspect_dirs(pathes):
        """
            Позволяет получить список содержимого директорий pathes

        :param pathes:      исходный список директорий
        :return:            список вложенных директорий
        """
        dirs = list()
        for path in pathes:
            for p in os.listdir(path):
                dirs.append(os.path.join(path, p))
        return dirs

    def get_user_dirs(self):
        """
            Делает листинг директорий в хранилище кэша

        :return:        список путей
        """
        return self.get_pathes(self.depth, self.base_path)

    def get_full_pathes(self, path):
        """
            Делает листинг директорий по пути path

        :param path:        путь, где искать папки
        :return:            список путей
        """
        return self.get_pathes(self.segm, path)

    def get_pathes(self, depth, data_path):
        """
            Выполняет листинг вложенных директорий

            Позволяет получить множество относительных путей, сформированных
            в результате листинга вложенных директорий внутри data_path.
            Принимает в качестве аргументов depth - насколько глубоко нужно
            делать листинг.

            Пример: depth = 2, data_path = '/var/data/'
            Результат: {'data_1/dir_1', 'data_2/dir_2'}

        :param depth:           "глубина" листинга (уровень вложенности)
        :param data_path:       путь, где необходимо выполнить листинг
        :return:                множество, содержащее пути к вложенным директориям
        """
        try:
            res = list()
            data_path = [data_path]
            if depth > 1:
                for i in range(depth-self.depth):
                    res = self.inspect_dirs(data_path)
                    data_path = res
            elif depth == 1:
                res = self.inspect_dirs(data_path)
            fried_res = {os.path.relpath(path, self.base_path) for path in res}
        except (OSError, IndexError, ValueError, TypeError) as ex:
            raise GetPathError(ex)
        return fried_res

    def add_in_filecache(self, path):
        """
            Добавляет запись в хранилище кэша

        :param path:        путь к данным
        """
        try:
            full_path = os.path.join(self.base_path, path)
            dir_xml = get_dir_xml(full_path)
            remove_date_time = get_remove_date(full_path, self.days)

            payload = {
                        'path': path,
                        'cache_type': self.type,
                        'structure': dir_xml,
                        'calc_region': True,
                        'remove_date_time': remove_date_time
                      }
            payload = json.dumps(payload, ensure_ascii=False)

            create_data_on_web(data_host=self.host, data_uri=self.data_uri, data=payload, auth_url=self.auth_url,
                               username=self.username, password=self.password, cook=self.cook)
        except (TypeError, WebAuthError, WebError) as ex:
            raise AddCacheError(ex)
        return None

    def update_filecache(self, id, path):
        """
            Обновляет запись в хранилище кэша

        :param path:        путь к данным
        """
        try:
            payload = {
                        'path': path,
                        'calc_region': True
                      }
            payload = json.dumps(payload, ensure_ascii=False)

            data_uri = 'storage/cache/{}'.format(str(id))
            update_data_on_web(data_host=self.host, data_uri=data_uri, data=payload, auth_url=self.auth_url,
                               username=self.username, password=self.password, cook=self.cook)
        except (WebError, TypeError) as ex:
            raise UpdateCacheError(ex)
        return None

    def check_filecache(self, path):
        """
            Получает записи из хранилища кэша по переданному пути

        :param path:        путь к родительской папке (пользователь, заявка)
        :return:            словарь со вложенной структорой записи кэша
        """
        try:
            data_uri = 'storage/cache?path={}&limit={}'.format(path, 1000)
            data = get_data_from_web(data_host=self.host, data_uri=data_uri, auth_url=self.auth_url,
                                     username=self.username, password=self.password, cook=self.cook)
            data = json.loads(data)['data']
            res = dict()
            interest = ['id', 'region_id']
            if data:
                for d in data:
                    new_data = {key: d[key] for key in interest}
                    res[d['path']] = new_data
        except (TypeError, WebError, KeyError) as ex:
            raise CheckFilecacheError(ex)
        return res

    def run(self, path):
        pass
