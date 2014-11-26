# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""
import csv
import logging
import locale
from json import dumps
from functools import wraps
from datetime import datetime, timedelta
from urlparse import urljoin
from threading import Lock
# pylint: disable=redefined-outer-name
from time import time
from cPickle import dumps as pickle_dumps
from hashlib import md5

from flask import Response
from lxml import etree

# pylint: disable=import-error
from presence_analyzer.main import app


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
LOCK = Lock()
CACHE = {}
locale.setlocale(locale.LC_COLLATE, 'pl_PL.UTF-8')


def is_expired(last_time, cache_time):
    """
    Checks if given time is expired.
    """
    return last_time + cache_time < time()


def cache(cache_time):
    """
    Decorator for memorize output from function for given time.
    """
    # pylint: disable=missing-docstring
    def _wrapper(func):
        @wraps(func)
        def __wrapper(*args, **kwargs):
            key = md5(
                pickle_dumps((func.__name__, args, kwargs))
            ).hexdigest()

            if key in CACHE and not is_expired(CACHE[key]['time'], cache_time):
                return CACHE[key]['data']

            CACHE[key] = {'time': time(), 'data': func()}
            return CACHE[key]['data']
        return __wrapper
    return _wrapper


def locker(func):
    """
    Decorator prevents for using function at the same time.
    """
    # pylint: disable=missing-docstring
    @wraps(func)
    def wrapper(*args, **kwargs):
        with LOCK:
            return func(*args, **kwargs)
    return wrapper


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


@locker
@cache(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


@locker
@cache(600)
def get_data_v2():
    """
    Return user id dict with names and links to their avatars.
    """
    xml = etree.parse(app.config['XML_FILE_PATH'])
    api_server = '%s://%s' % (
        xml.findtext('./server/protocol'), xml.findtext('./server/host')
    )

    data = []
    for user in xml.xpath('./users/user'):
        data.append(
            {
                'id': user.get('id'),
                'avatar': urljoin(api_server, user.findtext('avatar')),
                'name': user.findtext('name')
            }
        )

    data.sort(key=lambda x: x['name'], cmp=locale.strcoll)

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates interval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def seconds_to_hour(seconds):
    """
    Convert seconds to tuple (hour, minutes, seconds).
    """
    date = datetime(1, 1, 1) + timedelta(seconds=seconds)
    return date.timetuple()[3:6]
