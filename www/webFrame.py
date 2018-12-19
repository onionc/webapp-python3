#!/usr/bin/python

import asyncio
import os
import inspect
import functools
from urllib import parse
from aiohttp import web
from apis import APIError
# import pdb
from functions import logger


def get(path):
    """ get装饰器 @get('/path') """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator


def post(path):
    """ post装饰器 @post('/path') """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator


def get_required_kw_args(fn):
    """ 获取没有默认值的命名关键字参数 """
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        # 如果参数类型为(KEYWORD_ONLY)命名关键字参数, 无默认值则加入args
        if (param.kind == inspect.Parameter.KEYWORD_ONLY and
                param.default == inspect.Parameter.empty):
            args.append(name)
    return tuple(args)


def get_named_kw_args(fn):
    """ 获取所有命名关键字参数 """
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)


def has_named_kw_args(fn):
    """ 检查是否有命名关键字参数 """
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True


def has_var_kw_arg(fn):
    """ 检查是否有关键字参数 **kw """
    params = inspect.signature(fn).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


def has_request_arg(fn):
    """ 检查名为 request 的参数，并且是最后一个参数 """
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items():
        if name == 'request':
            found = True
            continue
        if (found and
                (param.kind != inspect.Parameter.VAR_POSITIONAL and
                    param.kind != inspect.Parameter.KEYWORD_ONLY and
                    param.kind != inspect.Parameter.VAR_KEYWORD)):
            raise ValueError(
                'request parameter must be the last named '
                'parameter in function: {0}{1}'.format(fn.__name__, str(sig)))
    return found


class RequestHandler(object):
    """ 请求处理器 """

    def __init__(self, app, fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)  # 是否有request
        self._has_var_kw_arg = has_var_kw_arg(fn)  # 是否有关键字参数 **kw
        self._has_named_kw_args = has_named_kw_args(fn)  # 是否有命名关键字参数
        self._named_kw_args = get_named_kw_args(fn)  # 获取所有 命名关键字 参数
        self._required_kw_args = get_required_kw_args(fn)  # 获取 没有默认值的命名关键字参数

    async def __call__(self, request):
        """ 分析请求, 整理参数 """
        kw = None
        if (self._has_var_kw_arg or
                self._has_named_kw_args or
                self._required_kw_args):
            # pdb.set_trace()
            if request.method == 'POST':
                # POST请求预处理，处理各种内容类型
                if not request.content_type:
                    return web.HTTPBadRequest(reason='Missing Content-type')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params = await request.json()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest(
                            reason='Json body must be object')
                    kw = params

                elif (ct.startswith('application/x-www-form-urlencoded') or
                        ct.startswith('multipart/form-data')):
                    params = await request.post()
                    kw = dict(**params)

                else:
                    return web.HTTPBadRequest(
                        reason='Unsupported Content-Type: {0}'
                        ''.format(request.content_type),
                        content_type=request.content_type
                        )

            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = {}
                    for k, v in parse.parse_qs(qs, True).items():
                        kw[k] = v[0]

        if kw is None:
            kw = dict(**request.match_info)
        else:
            if (not self._has_var_kw_arg) and self._named_kw_args:
                # 获取命名关键字
                copy = {}
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy
            for k, v in request.match_info.items():
                if k in kw:
                    logger.warning(
                        'Duplicate arg name in named '
                        'arg and kw args{0}'.format(k)
                        )
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        if self._required_kw_args:
            # 无默认值的关键字参数
            for name in self._required_kw_args:
                if not (name in kw):
                    return web.HTTPBadRequest(
                        reason='Missing argument:{0}'.format(name))
        if not kw:
            # stream request
            stream_data = await request.read()
            if stream_data:
                logger.info("xxxxxxxxxxxx{}".format(stream_data.decode('utf-8')))
                kw['data'] = stream_data.decode('utf-8')

        logger.info('call with args:{0}'.format(str(kw)))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)


def add_static(app):
    """ 添加静态资源路径 """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logger.info("add static {0} => {1}".format('/static/', path))


def add_route(app, fn):
    """ 将处理函数注册到web服务程序路由中 """
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in {0}'.format(fn))
    if (not asyncio.iscoroutinefunction(fn) and
            not inspect.isgeneratorfunction(fn)):
        fn = asyncio.coroutine(fn)
    logger.info("add route {0} {1} =>? {2}({3})".format(
        method,
        path,
        fn.__name__,
        ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, fn))


def add_routes(app, module_name):
    """ 自动注册符合条件的handler模块 """
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]
        mod = getattr(
            __import__(module_name[:n], globals(), locals(), [name]),
            name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)
