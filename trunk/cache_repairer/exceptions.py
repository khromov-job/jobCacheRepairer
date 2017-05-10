# -*- coding: utf-8 -*-

from job_launcher.exceptions import JobError


class CacheRepairerError(JobError):
    """
        Возникает в случае ошибок, возникающих в процессе работы джоба
    """
    def __init__(self, message=''):
        super().__init__(message)


class AddCacheError(CacheRepairerError):
    """
        Возникает в случае ошибок при добавлении нового кэша
    """
    def __init__(self, message=''):
        super().__init__('Ошибка при добавлении новой записи в кэш. {}'.format(message))


class UpdateCacheError(CacheRepairerError):
    """
        Возникает в случае ошибок при обновлении записи кэша
    """
    def __init__(self, message=''):
        super().__init__('Ошибка при обновлении кэша. {}'.format(message))


class CheckFilecacheError(CacheRepairerError):
    """
        Возникает в случае ошибок при получении записей кэша через API
    """

    def __init__(self, message=''):
        super().__init__('Ошибка при получении записей кэша. {}'.format(message))


class GetPathError(CacheRepairerError):
    """
        Возникает в случае ошибок, возникающих при получении листинга директории
    """

    def __init__(self, message=''):
        super().__init__('Ошибка при попытке выполнить листинг директории. {}'.format(message))