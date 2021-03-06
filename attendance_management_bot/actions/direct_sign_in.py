# !/bin/env python
# -*- coding: utf-8 -*-
"""
Handle the user's direct check-in
"""

__all__ = ['deal_sign_in_message', 'direct_sign_in']

import tornado.web
import asyncio
import logging
from attendance_management_bot.model.data import make_text, make_quick_reply
from attendance_management_bot.externals.send_message import push_message
from attendance_management_bot.actions.message import invalid_message, TimeStruct, \
    create_quick_replay_items
from attendance_management_bot.model.processStatusDBHandle \
    import get_status_by_user, delete_status_by_user_date

LOGGER = logging.getLogger("attendance_management_bot")


def deal_sign_in_message(sign_time, manual_flag):
    """
    Generate a message returned to the user when checking in.

    :param sign_time: The user's check-in time is a timestamp.
    :param manual_flag: Boolean value. True is manually enters time.
    :return: message content is a json.
    """
    call_back = "sign_in"
    if manual_flag:
        call_back = "manual_sign_in"

    user_time = TimeStruct(sign_time)

    text = make_text("Register the current time {date}"
                     .format(date=user_time.date_time.strftime('%A, %B %-d '
                                                               'at %-I:%M %P')))

    if manual_flag:
        text = make_text("Register the entered {date} as clock-in time?"
                         .format(date=user_time.date_time.strftime('%m, %-d %A '
                                                                   'at %-I:%M %P')))

    reply_items = create_quick_replay_items(
        "confirm_in&time=" + user_time.str_current_time_tick, call_back)

    text["quickReply"] = make_quick_reply(reply_items)

    return text


@tornado.gen.coroutine
def deal_sign_in(account_id, current_date, sign_time, manual_flag=False):
    content = get_status_by_user(account_id, current_date)

    if content is not None:
        status = content[0]
        process = content[1]
        if process is not None:
            return invalid_message()

        if status == "wait_in" or status == "in_done":
            delete_status_by_user_date(account_id, current_date)
            yield asyncio.sleep(1)

    return deal_sign_in_message(sign_time, manual_flag)


@tornado.gen.coroutine
def direct_sign_in(account_id, current_date, sign_time, _):
    """
    Handle the user's direct check-in.

    :param account_id: user account id.
    :param current_date: current date by local time.
    :param sign_time: Time when the user clicks to check-in.
    :param _: no use
    """
    content = yield deal_sign_in(account_id, current_date, sign_time)

    yield push_message(account_id, content)
