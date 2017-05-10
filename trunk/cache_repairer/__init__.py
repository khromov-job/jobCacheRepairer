# -*- encoding: utf-8 -*-

import os
import sys
import yaml
import logging.config
import argparse

from job_launcher.launcher import JobLauncher
from job_launcher import __unitype__

from cache_repairer.repairer_job import RepairerJob
from cache_repairer.misc import __uniapp__
from cache_repairer.database_manager import DatabaseManager
from cache_repairer.utils import check_time, get_dir_xml, update_last_run
from cache_repairer.exceptions import *


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', nargs='?', default='/etc/opt/jobCacheRepairer/',
                        help='Путь к директории с конфигурационными файлами.')
    parser.add_argument('-db', '--database', nargs='?', default=None,
                        help='Инициализцировать базу данных sqlite')
    args = parser.parse_args(sys.argv[1:])

    # Создание логгера
    with open(args.config + 'log_settings.yaml', 'r') as log_conf:
        log_dict = yaml.load(log_conf)
    logging.config.dictConfig(log_dict)
    logger = logging.getLogger(__name__)

    try:
        # Создание экземпляра лончера
        launcher = JobLauncher(args.config + 'settings.yaml')
        logger.info('Запуск приложения', extra={'unitype': __unitype__.format(code=''),
                                                'uniapp': __uniapp__.format(identifiers='')})
        # Получение настроек приложения
        settings = launcher.get_settings()
        params = settings['data_sources']['params']

        if args.database:
            db = DatabaseManager(args.database)
        else:
            db = DatabaseManager(params['db_path'])

        # Создание джоба
        job = RepairerJob(params)
        # Получение базового пути
        base_path = job.get_storage_path()

        # Если база пуста и прошло 12 часов с момента последнего запуска, заполнить БД
        if check_time() and not db.select_all_data():
            # Формирование листинга директорий с учетом количества сегментов
            listing = job.get_user_dirs()
            for path in listing:
                db.add(path)
            logger.info('База данных заполнена. Всего записей: {}'.format(db.select_last()[0]),
                        extra={'unitype': __unitype__.format(code=''),
                               'uniapp': __uniapp__.format(identifiers='')})

        # Если база не пуста и прошло более 12 часов с момента последнего запуска, выполнить работу
        if check_time():
            id_last = db.select_last()[0]
            while id_last > 0:
                try:
                    # Берем очередную директорию пользователя из базы данных и формируем полный путь
                    path = db.select(id_last)[1]
                    logger.info('Обработка директории {}'.format(path),
                                extra={'unitype': __unitype__.format(code=''),
                                       'uniapp': __uniapp__.format(identifiers='')})
                    full_path = os.path.join(base_path, path)
                    # Получаем листинг директорий для данного пользователя
                    local_dirs = job.get_full_pathes(full_path)
                    # Получаем директории для этого пользователя, хранящиеся в API
                    api_dirs = job.check_filecache(path)

                    try:
                        for cache_path in local_dirs:
                            if cache_path in api_dirs:
                                # Получаем данные из API, используя в качестве ключа путь к кэшу
                                api_current = api_dirs.get(cache_path)
                                # Проверяем наличие region_id у конкретной записи и при отсутствии обновляем запись
                                if not api_current['region_id']:
                                    cache_id = api_current['id']
                                    job.update_filecache(cache_id, cache_path)
                                    logger.info('Обновлена запись id = {}, path = "{}"'
                                                .format(cache_id, cache_path),
                                                extra={'unitype': __unitype__.format(code=''),
                                                       'uniapp': __uniapp__.format(identifiers='')})
                            else:
                                # Создаем новую запись
                                job.add_in_filecache(cache_path)
                                logger.info('Добавлена новая запись path = "{}"'.format(cache_path),
                                            extra={'unitype': __unitype__.format(code=''),
                                                   'uniapp': __uniapp__.format(identifiers='')})
                    except CacheRepairerError as ex:
                        logger.error(ex)
                        continue
                    else:
                        # В случае успешной обработки удаляем запись из БД
                        db.delete(id_last)
                    id_last -= 1

                except CacheRepairerError as ex:
                    logger.error(ex)
                    break

            update_last_run()
            logger.info('Обновление значения времени последнего запуска...',
                        extra={'unitype': __unitype__.format(code=''),
                               'uniapp': __uniapp__.format(identifiers='')})

        else:
            logger.info('Время очередной проверки еще не пришло',
                        extra={'unitype': __unitype__.format(code=''),
                               'uniapp': __uniapp__.format(identifiers='')})
        logger.info('Приложение успешно завершило свою работу',
                    extra={'unitype': __unitype__.format(code=''),
                           'uniapp': __uniapp__.format(identifiers='')})

    except Exception as ex:
        logger.error('Получено исключение: {}'.format(ex),
                     extra={'unitype': __unitype__.format(code=''),
                            'uniapp': __uniapp__.format(identifiers='')}, exc_info=False)
        logger.warning('Работа приложения аварийно завершена',
                       extra={'unitype': __unitype__.format(code=''),
                              'uniapp': __uniapp__.format(identifiers='')})


if __name__ == "__main__":
    main()
