# -*- coding: utf-8 -*-
"""
Defines views.
"""
import logging
import calendar

from flask import redirect, abort

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean,
    group_by_weekday,
    seconds_since_midnight,
    seconds_to_hour
)


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/static/presence_weekday.html')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns avg start and end time of the user.
    """
    data = get_data().get(user_id, None)
    if user_id is None:
        log.debug('User %s not found!', user_id)
        abort(404)

    result = {x: {'start': [], 'end': []} for x in xrange(7)}

    for date, val in data.iteritems():
        result[date.weekday()]['start'].append(
            seconds_since_midnight(val['start'])
        )
        result[date.weekday()]['end'].append(
            seconds_since_midnight(val['end'])
        )

    result = [
        (
            calendar.day_abbr[weekday],
            seconds_to_hour(mean(val['start'])),
            seconds_to_hour(mean(val['end']))
        )
        for weekday, val in result.iteritems()
    ]

    return result
