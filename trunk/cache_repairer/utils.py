# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import os, platform
from xml.sax.saxutils import quoteattr as xml_quoteattr

BASE = os.path.dirname(os.path.realpath(__file__))


def check_time():
    """
        Проверяет, прошло ли определенное количество времени между текущим
        значением времени и значением, записанным в файле

    :return:    bool
    """
    with open(os.path.dirname(BASE) + '/last_run.txt', 'r') as f:
        date = f.read()
    fmt = '%Y-%m-%d %H:%M:%S'
    last_run = datetime.strptime(date, fmt)
    now_time = datetime.now()
    delta = now_time - last_run
    return delta > timedelta(hours=12)


def update_last_run():
    """
        Перезаписывает значение времени в файле на текущее значение
    """
    with open(os.path.dirname(BASE) + '/last_run.txt', 'w') as f:
        f.write(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


def get_remove_date(path, store_days):
    """
        Возвращает дату и время удаления кэша

    :param path:        путь к директории с кэшем
    :param store_days:  срок хранения в днях
    :return:            дата и время в строковом формате
    """
    if platform.system() == 'Windows':
        date = os.path.getctime(path)
    else:
        stat = os.stat(path)
        date = stat.st_mtime
    creation_date = datetime.fromtimestamp(date)
    remove_date = creation_date + timedelta(store_days)
    return remove_date.replace(microsecond=0).isoformat()


def get_dir_xml(path, i=0):
    """
        Создает структуру xml на основе заданной директории и вложенных в нее директорий

    :param path:        путь к директории
    :param i:
    :return:            xml - структура
    """
    if i == 0:
        result = '<?xml version="1.1" encoding="UTF-8"?>\n' + '<Structure>\n'
    elif len(os.listdir(path)) == 0:
        result = '<Dir name=%s/>\n' % xml_quoteattr(os.path.basename(path))
        return result
    else:
        result = '<Dir name=%s>\n' % xml_quoteattr(os.path.basename(path))
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            result += '\n'.join('  ' + line for line in
                                get_dir_xml(os.path.join(path, item), i + 1).
                                split('\n')[:-1])
            result += '\n'
        elif os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            result += '  <File name=%s size=%s/>\n' % (
                xml_quoteattr(item), '"' + str(size) + '"')
    if i == 0:
        result += '</Structure>\n'
    else:
        result += '</Dir>\n'
    return result

# print(get_dir_xml('/var/data/ext_product_delivery/publication/job_2/cache_cleaner3/2017-03-20/task_Район_Бутово'))
# print(get_remove_date('/var/data/ext_product_delivery/publication/job_2/cache_cleaner3/2017-03-20/task_Район_Бутово', 21))
