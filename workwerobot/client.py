# -*- coding: utf-8 -*-

import time
import requests
from six.moves import urllib

from requests.compat import json as _json
from workwerobot.utils import to_text
from workwerobot.replies import Article


class ClientException(Exception):
    pass


def check_error(json):
    """
    检测微信公众平台返回值中是否包含错误的返回码。
    如果返回码提示有错误，抛出一个 :class:`ClientException` 异常。否则返回 True 。
    """
    if "errcode" in json and json["errcode"] != 0:
        raise ClientException("{}: {}".format(json["errcode"], json["errmsg"]))
    return json


class Client(object):
    """
    微信 API 操作类
    通过这个类可以方便的通过微信 API 进行一系列操作，比如主动发送消息、创建自定义菜单等
    """

    def __init__(self, config):
        self.config = config
        self._token = None
        self.token_expires_at = None

    @property
    def appid(self):
        return self.config.get("CORP_ID", None)

    @property
    def appsecret(self):
        return self.config.get("SECRET", None)

    @staticmethod
    def _url_encode_files(file):
        if hasattr(file, "name"):
            file = (urllib.parse.quote(file.name), file)
        return file

    def request(self, method, url, **kwargs):
        if "params" not in kwargs:
            kwargs["params"] = {"access_token": self.token}
        if isinstance(kwargs.get("data", ""), dict):
            body = _json.dumps(kwargs["data"], ensure_ascii=False)
            body = body.encode('utf8')
            kwargs["data"] = body

        r = requests.request(method=method, url=url, **kwargs)
        r.raise_for_status()
        r.encoding = "utf-8"
        json = r.json()
        if check_error(json):
            return json

    def get(self, url, **kwargs):
        return self.request(method="get", url=url, **kwargs)

    def post(self, url, **kwargs):
        if "files" in kwargs:
            # Although there is only one key "media" possible in "files" now,
            # we decide to check every key to support possible keys in the future
            # Fix chinese file name error #292
            kwargs["files"] = dict(
                zip(
                    kwargs["files"],
                    map(self._url_encode_files, kwargs["files"].values())
                )
            )
        return self.request(method="post", url=url, **kwargs)

    def grant_token(self):
        """
        获取 Access Token。

        :return: 返回的 JSON 数据包
        """
        return self.get(
            url="https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            params={
                "corpid": self.appid,
                "corpsecret": self.appsecret
            }
        )

    def get_access_token(self):
        """
        判断现有的token是否过期。
        用户需要多进程或者多机部署可以手动重写这个函数
        来自定义token的存储，刷新策略。

        :return: 返回token
        """
        if self._token:
            now = time.time()
            if self.token_expires_at - now > 60:
                return self._token
        json = self.grant_token()
        self._token = json["access_token"]
        self.token_expires_at = int(time.time()) + json["expires_in"]
        return self._token

    @property
    def token(self):
        return self.get_access_token()

    def get_ip_list(self):
        """
        获取微信服务器IP地址。

        :return: 返回的 JSON 数据包
        """
        return self.get(url="https://qyapi.weixin.qq.com/cgi-bin/getcallbackip")

    def create_menu(self, menu_data):
        """
        创建自定义菜单::

            client.create_menu({
                "button":[
                    {
                        "type":"click",
                        "name":"今日歌曲",
                        "key":"V1001_TODAY_MUSIC"
                    },
                    {
                        "type":"click",
                        "name":"歌手简介",
                        "key":"V1001_TODAY_SINGER"
                    },
                    {
                        "name":"菜单",
                        "sub_button":[
                            {
                                "type":"view",
                                "name":"搜索",
                                "url":"http://www.soso.com/"
                            },
                            {
                                "type":"view",
                                "name":"视频",
                                "url":"http://v.qq.com/"
                            },
                            {
                                "type":"click",
                                "name":"赞一下我们",
                                "key":"V1001_GOOD"
                            }
                        ]
                    }
                ]})

        :param menu_data: Python 字典
        :return: 返回的 JSON 数据包
        """
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/menu/create",
            data=menu_data,
            params={"agentid": self.config["AGENT_ID"]}
        )

    def get_menu(self):
        """
        查询自定义菜单。

        :return: 返回的 JSON 数据包
        """
        return self.get("https://qyapi.weixin.qq.com/cgi-bin/menu/get",params={"agentid":self.config["AGENT_ID"]})

    def delete_menu(self):
        """
        删除自定义菜单。

        :return: 返回的 JSON 数据包
        """
        return self.get("https://qyapi.weixin.qq.com/cgi-bin/menu/delete",params={"agentid":self.config["AGENT_ID"]})


    def upload_media(self, media_type, media_file):
        """
        上传临时多媒体文件。

        :param media_type: 媒体文件类型，分别有图片（image）、语音（voice）、视频（video）和缩略图（thumb）
        :param media_file: 要上传的文件，一个 File-object
        :return: 返回的 JSON 数据包
        """
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/media/upload",
            params={
                "access_token": self.token,
                "type": media_type
            },
            files={"media": media_file}
        )

    def download_media(self, media_id):
        """
        下载临时多媒体文件。

        :param media_id: 媒体文件 ID
        :return: requests 的 Response 实例
        """
        return requests.get(
            url="https://qyapi.weixin.qq.com/cgi-bin/media/get",
            params={
                "access_token": self.token,
                "media_id": media_id
            }
        )

    def upload_news_picture(self, file):
        """
        上传图文消息内的图片。

        :param file: 要上传的文件，一个 File-object
        :return: 返回的 JSON 数据包
        """
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/media/uploadimg",
            params={"access_token": self.token},
            files={"media": file}
        )

    def create_department(self, name, parentid, order=None, id=None):
        """
        创建分组。

        :param name: 分组名字（30个字符以内）
        :return: 返回的 JSON 数据包

        """
        name = to_text(name)
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/departments/create",
            data={
                "name": name,
                "parentid": parentid,
                "order": order,
                "id": id

            }
        )

    def get_departments(self):
        """
        查询所有分组。

        :return: 返回的 JSON 数据包
        """
        return self.get("https://qyapi.weixin.qq.com/cgi-bin/departments/list")


    def update_department(self, department_id, name):
        """
        修改分组名。

        :param department_id: 分组 ID，由微信分配
        :param name: 分组名字（30个字符以内）
        :return: 返回的 JSON 数据包
        """
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/departments/update",
            data={"department": {
                "id": int(department_id),
                "name": to_text(name)
            }}
        )

    def delete_department(self, department_id):
        """
        删除分组。

        :param department_id: 要删除的分组的 ID
        :return: 返回的 JSON 数据包
        """
        return self.get(
            url="https://qyapi.weixin.qq.com/cgi-bin/departments/delete",
            params={
                "id": department_id
            }
        )

    def get_user_info(self, user_id):
        """
        获取用户基本信息。

        :param user_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :param lang: 返回国家地区语言版本，zh_CN 简体，zh_TW 繁体，en 英语
        :return: 返回的 JSON 数据包
        """
        return self.get(
            url="https://qyapi.weixin.qq.com/cgi-bin/user/get",
            params={
                "access_token": self.token,
                "userid": user_id,
            }
        )

    def send_text_message(self, content, user_id=None):
        """
        发送文本消息。

        :param user_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :param content: 消息正文
        :param kf_account: 发送消息的客服账户，默认值为 None，None 为不指定
        :return: 返回的 JSON 数据包
        """
        data = {
            "touser": user_id,
            "msgtype": "text",
            "agentid": self.config["AGENT_ID"],
            "text": {
                "content": content
            }
        }
        return self.post(
            url=" https://qyapi.weixin.qq.com/cgi-bin/message/send",
            data=data
        )

    def send_image_message(self, media_id, user_id=None):
        """
        发送图片消息。

        :param user_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :param media_id: 图片的媒体ID。 可以通过 :func:`upload_media` 上传。
        :param kf_account: 发送消息的客服账户，默认值为 None，None 为不指定
        :return: 返回的 JSON 数据包
        """
        data = {
            "touser": user_id,
            "msgtype": "image",
            "agentid": self.config["AGENT_ID"],
            "image": {
                "media_id": media_id
            }
        }
        return self.post(
            url=" https://qyapi.weixin.qq.com/cgi-bin/message/send",
            data=data
        )

    def send_voice_message(self, media_id, user_id=None):
        """
        发送语音消息。

        :param user_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :param media_id: 发送的语音的媒体ID。 可以通过 :func:`upload_media` 上传。
        :param kf_account: 发送消息的客服账户，默认值为 None，None 为不指定
        :return: 返回的 JSON 数据包
        """
        data = {
            "touser": user_id,
            "msgtype": "voice",
            "agentid": self.config["AGENT_ID"],
            "voice": {
                "media_id": media_id
            }
        }
        return self.post(
            url=" https://qyapi.weixin.qq.com/cgi-bin/message/send",
            data=data
        )

    def send_video_message(
        self, media_id, title=None, description=None, user_id=None
    ):
        """
        发送视频消息。

        :param user_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :param media_id: 发送的视频的媒体ID。 可以通过 :func:`upload_media` 上传。
        :param title: 视频消息的标题
        :param description: 视频消息的描述
        :return: 返回的 JSON 数据包
        """
        video_data = {
            "media_id": media_id,
        }
        if title:
            video_data["title"] = title
        if description:
            video_data["description"] = description
        data = {"touser": user_id, "msgtype": "video","agentid": self.config["AGENT_ID"], "video": video_data}
        return self.post(
            url=" https://qyapi.weixin.qq.com/cgi-bin/message/send",
            data=data
        )

    def send_file_message(
        self,
        user_id,
        media_id
    ):
        """
        发送音乐消息。
        注意如果你遇到了缩略图不能正常显示的问题， 不要慌张； 目前来看是微信服务器端的问题。
        对此我们也无能为力 ( `#197 <https://github.com/whtsky/WeRoBot/issues/197>`_ )

        :param user_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :param url: 音乐链接
        :param hq_url: 高品质音乐链接，wifi环境优先使用该链接播放音乐
        :param thumb_media_id: 缩略图的媒体ID。 可以通过 :func:`upload_media` 上传。
        :param title: 音乐标题
        :param description: 音乐描述
        :return: 返回的 JSON 数据包
        """
        data = {"touser": user_id, "msgtype": "file","agentid": self.config["AGENT_ID"], "file": media_id}
        return self.post(
            url=" https://qyapi.weixin.qq.com/cgi-bin/message/send",
            data=data
        )

    def send_article_message(self, articles, user_id=None):
        """
        发送图文消息::

            articles = [
                {
                    "title":"Happy Day",
                    "description":"Is Really A Happy Day",
                    "url":"URL",
                    "picurl":"PIC_URL"
                },
                {
                    "title":"Happy Day",
                    "description":"Is Really A Happy Day",
                    "url":"URL",
                    "picurl":"PIC_URL"
                }
            ]
            client.send_acticle_message("user_id", acticles)

        :param user_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :param articles: 一个包含至多8个 article 字典或 Article 对象的数组
        :param kf_account: 发送消息的客服账户，默认值为 None，None 为不指定
        :return: 返回的 JSON 数据包
        """
        if isinstance(articles[0], Article):
            formatted_articles = []
            for article in articles:
                result = article.args
                result["picurl"] = result.pop("img")
                formatted_articles.append(result)
        else:
            formatted_articles = articles
        data = {
            "touser": user_id,
            "msgtype": "news",
            "agentid": self.config["AGENT_ID"],
            "news": {
                "articles": formatted_articles
            }
        }

        return self.post(
            url=" https://qyapi.weixin.qq.com/cgi-bin/message/send",
            data=data
        )

    def send_markdown_message(self, text, user_id=None):
        """
        发送markdown消息。

        :param user_id: 用户 ID 。 就是你收到的 `Message` 的 source
        :param media_id: 媒体文件 ID
        :param kf_account: 发送消息的客服账户，默认值为 None，None 为不指定
        :return: 返回的 JSON 数据包
        """
        data = {
            "touser": user_id,
            "msgtype": "markdown",
            "agentid": self.config["AGENT_ID"],
            "markdown": {
                "content": text
            }
        }

        return self.post(
            url=" https://qyapi.weixin.qq.com/cgi-bin/message/send",
            data=data
        )

    def create_tag(self, tag_name):
        """
        创建一个新标签

        :param tag_name: 标签名
        :return: 返回的 JSON 数据包
        """
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/tags/create",
            data={
                "tagname": tag_name
            }
        )

    def get_tags(self):
        """
        获取已经存在的标签

        :return: 返回的 JSON 数据包
        """
        return self.get(url="https://qyapi.weixin.qq.com/cgi-bin/tag/list")

    def update_tag(self, tag_id, tag_name):
        """
        修改标签

        :param tag_id: 标签 ID
        :param tag_name: 新的标签名
        :return: 返回的 JSON 数据包
        """
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/tags/update",
            data={
                "id": tag_id,
                "name": tag_name
            }
        )

    def delete_tag(self, tag_id):
        """
        删除标签

        :param tag_id: 标签 ID
        :return: 返回的 JSON 数据包
        """
        return self.get(
            url="https://qyapi.weixin.qq.com/cgi-bin/tags/delete",
            params={
                "id": tag_id,
            }
        )

    def get_users_by_tag(self, tag_id):
        """
        获取标签下粉丝列表

        :param tag_id: 标签 ID
        :param next_open_id: 第一个拉取用户的 OPENID，默认从头开始拉取
        :return: 返回的 JSON 数据包
        """
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/user/tag/get",
            data={
                "tagid": tag_id,
            }
        )

    def tag_users(self, tag_id, user_id_list):
        """
        批量为用户打标签

        :param tag_id: 标签 ID
        :param open_id_list: 包含一个或多个用户的 OPENID 的列表
        :return: 返回的 JSON 数据包
        """
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/tag/addtagusers",
            data={
                "userlist": user_id_list,
                "tagid": tag_id
            }
        )

    def untag_users(self, tag_id, user_id_list):
        """
        批量为用户取消标签

        :param tag_id: 标签 ID
        :param open_id_list: 包含一个或多个用户的 OPENID 的列表
        :return: 返回的 JSON 数据包
        """
        return self.post(
            url="https://qyapi.weixin.qq.com/cgi-bin/tag/deltagusers",
            data={
                "userlist": user_id_list,
                "tagid": tag_id
            }
        )
