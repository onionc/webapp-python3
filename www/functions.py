# !/usr/bin/python
# -*- coding: utf-8 -*-
""" public function and variable """

import re
import hashlib
import time
import logging 
import logging.config
from apis import APIError, APIPermissionError
import sys
import traceback

# 日志配置
logging.config.fileConfig('./config/log.conf')
logger = logging.getLogger('root')
# 调试未捕获异常用 logger.basicConfig(level=logger.INFO)

# variable
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')
_COOKIE_NAME = 'cowpeas_blog'
_COOKIE_KEY = 'cookie secret cowpea copyright'


def get_avatar(key):
    """ 通过key获取唯一头像 """
    # 头像地址
    _AVATAR_URL = 'http://www.gravatar.com/avatar/'
    return "{0}/{1}?d=monsterid&s=100".format(_AVATAR_URL, key)


def get_page_index(page):
    """ 返回有效的页码 """
    return int(page) if int(page)>0 else 1


def user2cookie(user, max_age):
    """ 加密生成cookie """
    expires = str(int(time.time()) + max_age)
    s = "{}-{}-{}-{}".format(user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


async def cookie2user(cookie_str):
    """ 从cookie解析用户数据 """
    
    import models
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await models.User.find(uid)
        if user is None:
            return None
        s = "{}-{}-{}-{}".format(uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            print(L)
            logger.error('invalid sha1, uid:{0}'.format(uid))
            return None
        user.passwd = '****'
        return user
    except Exception as e:
        logger.exception(e)
        return None

def check_admin(request):
    """ 检测用户 """
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

def text2html(text):
    """ 格式化字符，转义& < >"""
    lines = map(lambda s:"<p>{0}</p>".format(s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: strip() != '', text.split('\n'))))


def my_exception_hook(exctype, value, tb):
    """ 捕获异常 """
    err_msg = ' '.join(traceback.format_exception(exctype, value, tb))
    logger.warn(' !! exception hook !!')
    #logger.warn("type:{},value:{}\n traceback:{}".format(exctype, value, traceback.print_exc()))    
    logger.warn(err_msg)    

def exception_set(flag):
    """ 设置捕获异常 """
    if flag:
        sys.excepthook = my_exception_hook
    else:
        sys.excepthook = sys.__excepthook__

