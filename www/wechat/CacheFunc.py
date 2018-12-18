# coding:utf-8

from module.rediscache.Cache import Cache
from config.env import CONF
from functions import logger
from urllib import request
import json


@Cache(key=CONF['wechat']['access_token_key'])
def access_token_cache():
    """ access token 缓存 """
    try:
        postUrl = CONF['url']['access_token_url']
        urlResp = request.urlopen(postUrl)
        urlResp = json.loads(urlResp.read())
        logger.debug("[wechat] access_token: {} {}".format(urlResp, postUrl))
        return urlResp['access_token']
    except Exception:
        logger.warning("[wechat] access_token error: {} {}".format(urlResp, postUrl))
        return ''


def get_access_token():
    """ 获取 access token """
    access_token_cache.set_attr(ttl=30)
    return access_token_cache()
