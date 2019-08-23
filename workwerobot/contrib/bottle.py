# -*- coding: utf-8 -*-
from __future__ import absolute_import
from urllib.parse import unquote
from bottle import request, HTTPResponse

try:
    import html
except ImportError:
    import cgi as html


def make_view(robot):
    """
    为一个 BaseRoBot 生成 Bottle view。

    Usage ::

        from werobot import WeRoBot

        robot = WeRoBot(token='token')


        @robot.handler
        def hello(message):
            return 'Hello World!'

        from bottle import Bottle
        from werobot.contrib.bottle import make_view

        app = Bottle()
        app.route(
            '/robot',  # WeRoBot 挂载地址
            ['GET', 'POST'],
            make_view(robot)
        )


    :param robot: 一个 BaseRoBot 实例
    :return: 一个标准的 Bottle view
    """

    def werobot_view(*args, **kwargs):

        if request.method == 'GET':
            request.query.echostr = unquote(request.query.echostr)
            if not robot.check_signature(
                    request.query.timestamp, request.query.nonce,
                    request.query.echostr, request.query.msg_signature
            ):
                return HTTPResponse(
                    status=403,
                    body=robot.make_error_page(html.escape(request.url))
                )
            return robot.crypto.decrypt_message(
                timestamp=request.query.timestamp,
                nonce=request.query.nonce,
                msg_signature=request.query.msg_signature,
                encrypt_msg=request.query.echostr
            )
        else:
            body = request.body.read()
            message = robot.parse_message(
                body,
                timestamp=request.query.timestamp,
                nonce=request.query.nonce,
                msg_signature=request.query.msg_signature
            )
            print(message)
            return robot.get_encrypted_reply(message)

    return werobot_view
