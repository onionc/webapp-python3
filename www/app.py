# !/usr/bin/python
# conding:utf-8
import asyncio
import os
import json
import time
import orm

from datetime import datetime
from aiohttp import web
from jinja2 import Environment, FileSystemLoader
from webFrame import add_routes, add_static
from functions import logger
from config.env import CONF

import functions as Glo
# 开启异常捕获
Glo.exception_set(True)


def init_jinja2(app, **kw):
    logger.debug('init jinja2...')
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)),
            'templates')
    logger.debug('set jinja2 template path: {}'.format(path))
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env


async def logger_factory(app, handler):
    async def loggerx(request):
        logger.debug('Request:{} {}'.format(request.method, request.path))
        return (await handler(request))
    return loggerx


async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswitch('application/json'):
                request.__data__ = await request.json()
                logger.debug('request json:{}'.format(request.__data__))
            elif request.content_type.startswith(
                    'application/x-www-form-urlencode'):
                request.__data__ = await request.post()
                logger.debug('request post:{}'.format(request.__data__))
        return (await handler(request))
    return parse_data


async def response_factory(app, handler):
    """ 响应工厂 """
    async def response(request):
        logger.debug('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                """ 重定向链接 """
                return web.HTTPFound(r[9:])
            # 字符串还可用直接返回，用于wx验证
            resp = web.Response(body=r.encode('utf-8'))
            logger.debug("r=%s" % r)
            resp.content_type = 'text/html;charset=utf-8'
            return resp

        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(
                        body=json.dumps(
                            r,
                            ensure_ascii=False,
                            default=lambda o: o.__dict__).encode('utf-8')
                    )
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                r['__user__'] = request.__user__
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and (100 <= r < 600):
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and (100 <= r < 600):
                return web.Response(t, str(m))
        # default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response


async def auth_factory(app, handler):
    """ 权限工厂，解析cookie,将用户绑定到request对象 """
    async def auth(request):
        logger.debug("check user: {0} {1}".format(request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(Glo._COOKIE_NAME)
        if cookie_str:
            user = await Glo.cookie2user(cookie_str)
            if user:
                logger.debug('set current user: {0}'.format(user.email)) 
                request.__user__ = user
        if (request.path.startswith('/manage/') and
                (request.__user__ is None or not request.__user__.admin)):
            return web.HTTPFound('/signin')
        return (await handler(request))
    return auth


def datetime_filter(t):
    """ datetime 过滤器 """
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    elif delta < 3600:
        return u'{}分钟前'.format(delta // 60)
    elif delta < 86400:
        return u'{}小时前'.format(delta // 3600)
    elif delta < 604800:
        return u'{}天前'.format(delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'{0}年{1}月{2}日'.format(dt.year, dt.month, dt.day)


async def init(loop):
    await orm.create_pool(
        loop=loop,
        host=CONF['db']['host'],
        port=CONF['db']['port'],
        user=CONF['db']['user'],
        password=CONF['db']['password'],
        db=CONF['db']['dbName']
    )

    app = web.Application(loop=loop, middlewares=[
        logger_factory, auth_factory, response_factory
    ])

    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
    try:
        srv = await loop.create_server(
            app.make_handler(),
            CONF['host'],
            CONF['port'])
    except Exception as e:
        logger.error(e)

    logger.info(f"server started at http://{CONF['host']}:{CONF['port']}")
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
