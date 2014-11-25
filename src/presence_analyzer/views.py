# -*- coding: utf-8 -*-
"""
Defines views.
"""
import logging
import calendar

from flask import redirect, abort, url_for
# pylint: disable=no-name-in-module, import-error
from flask.ext.mako import render_template
from mako.exceptions import TopLevelLookupException

from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    get_data_v2,
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
    return redirect(
        url_for('template_param', template='presence_weekday.html')
    )


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def api_users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v2/users', methods=['GET'])
@jsonify
def api_users_v2_view():
    """
    Users listing with avatars for dropdown.
    """
    return get_data_v2()


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def api_mean_time_weekday(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data().get(user_id)
    if data is None:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data)
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def api_presence_weekday(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data().get(user_id)
    if data is None:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data)
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def api_presence_start_end(user_id):
    """
    Returns avg start and end time of the user.
    """
    data = get_data().get(user_id)
    if data is None:
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


@app.route('/<template>')
def template_param(template):
    """
    Function that render template if exists. If not then abort with 404.
    """
    try:
        return render_template(template)
    except TopLevelLookupException:
        abort(404)


@app.route('/api/v1/mean_start_end/<int:user_id>', methods=['GET'])
@jsonify
def api_mean_start_end(user_id):
    """
    Returns avg start and end time of the user.
    """
    data = get_data().get(user_id)
    if data is None:
        log.debug('User %s not found!', user_id)
        abort(404)

    result = {'start': [], 'end': []}

    for val in data.itervalues():
        result['start'].append(
            seconds_since_midnight(val['start'])
        )
        result['end'].append(
            seconds_since_midnight(val['end'])
        )

    result = [
        seconds_to_hour(mean(result['start'])),
        seconds_to_hour(mean(result['end']))
    ]

    return result
