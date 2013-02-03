# -*- coding: utf-8 -*-
import werobot.reply
import werobot.test
from werobot.utils import to_unicode


def test_text_render():
    message = werobot.test.make_text_message('test')
    reply = werobot.reply.TextReply(message, content='hello', time=1359803261)
    reply_message = """
    <xml>
    <ToUserName><![CDATA[test]]></ToUserName>
    <FromUserName><![CDATA[test]]></FromUserName>
    <CreateTime>1359803261</CreateTime>
    <MsgType><![CDATA[text]]></MsgType>
    <Content><![CDATA[hello]]></Content>
    <FuncFlag>0</FuncFlag>
    </xml>
    """.strip().replace(" ", "").replace("\n", "")
    result = reply.render().strip().replace(" ", "").replace("\n", "")
    assert result == to_unicode(reply_message)


def test_create_reply():
    message = werobot.test.make_text_message('test')
    reply = werobot.reply.create_reply('hi', message)
    assert reply  # Just make sure that func works.