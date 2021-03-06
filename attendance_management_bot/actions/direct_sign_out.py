# !/bin/env python
# -*- coding: utf-8 -*-
"""
Handle the user's direct check-out
"""

__all__ = ['deal_sign_out_message', 'deal_sign_out']

import tornado.web
import logging
import asyncio
from attendance_management_bot.model.data import make_text, make_quick_reply
from attendance_management_bot.externals.send_message import push_messages
from attendance_management_bot.actions.message import invalid_message, \
    TimeStruct, create_quick_replay_items, number_message
from attendance_management_bot.model.calendarDBHandle \
    import get_schedule_by_user
from attendance_management_bot.model.processStatusDBHandle \
    import get_status_by_user, set_status_by_user_date

LOGGER = logging.getLogger("attendance_management_bot")


def deal_sign_out_message(sign_time, manual_flag=False):
    """
    Generate a message returned to the user when checking out.

    :param sign_time: The user's check-in time is a timestamp.
    :param manual_flag: Boolean value. True is manually enters time.
    :return: message content is a json.
    """
    call_back = "sign_out"
    if manual_flag:
        call_back = "manual_sign_out"

    user_time = TimeStruct(sign_time)

    text = make_text("Register the current time {date}"
                     .format(date=user_time.date_time.strftime('%A, %B %-d '
                                                               'at %-I:%M %P')))

    if manual_flag:
        text = make_text("Register the entered {date} as clock-out time?"
                         .format(date=user_time.date_time.strftime('%m, %-d %A '
                                                                   'at %-I:%M %P')))

    reply_items = create_quick_replay_items(
        "confirm_out&time=" + user_time.str_current_time_tick, call_back)

    text["quickReply"] = make_quick_reply(reply_items)
    return text


@tornado.gen.coroutine
def deal_sign_out(account_id, current_date, sign_time, manual_flag=False):
    content = get_status_by_user(account_id, current_date)
    process = None
    if content is not None:
        status = content[0]
        process = content[1]

    if process is None or process != "sign_in_done":
        return [invalid_message()], True

    if status == "wait_out" or status == "out_done":
        set_status_by_user_date(account_id, current_date, status="in_done")
        yield asyncio.sleep(1)

    info = get_schedule_by_user(account_id, current_date)
    if info is None:
        raise HTTPError(500, "Internal data error")
    begin_time_st = info[1]
    user_time = TimeStruct(sign_time)
    if int(user_time.str_current_time_tick) < begin_time_st:
        set_status_by_user_date(account_id, current_date, status="wait_out")
        return number_message(), False

    return [deal_sign_out_message(sign_time, manual_flag)], True


@tornado.gen.coroutine
def direct_sign_out(account_id, current_date, sign_time, _):
    """
    Handle the user's direct check-out.

    :param account_id: user account id.
    :param current_date: current date by local time.
    :param sign_time: Time when the user clicks to check-out.
    :param _: no use
    """
    content, _ = yield deal_sign_out(account_id, current_date, sign_time)

    yield push_messages(account_id, content)
