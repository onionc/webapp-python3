#!/usr/bin/python
""" default configurations """

CONF = {
    'debug': True,
    'host': '127.0.0.1',
    'port': 80,
    'db': {
        'host': '127.0.0.1',
        'port': 3306,
        'user': 'test',
        'password': '****',
        'dbName': 'test'
    },
    'session': {
        'secret': 'cowpea'
    },
    'wechat': {
        'token': 'xxxx',  # 微信服务器验证token
        'appid': 'xxxx',
        'secret': 'xxxx',
        'access_token_key': 'access_token'
    },
    'url': {
    }

}

# 获取access token url
CONF['url']['access_token_url'] = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={CONF['wechat']['appid']}&secret={CONF['wechat']['secret']}"