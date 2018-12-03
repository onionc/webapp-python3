#!/usr/bin/python

""" url handlers """

import json
import logging
import asyncio
import hashlib
import mistune

from aiohttp import web
from webFrame import get, post
from models import User, Comment, Blog, next_id
from apis import Page, APIError, APIValueError
import functions as Glo
from functions import logger

# 首页
@get('/')
async def index(request):
    users = await User.findAll()
    return {
        '__template__': 'index.html',
        'users': users
    }

# 用户注册api
@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not Glo._RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not Glo._RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = await User.findAll('email=?', [email])
    if len(users)>0:
        raise APIError('register:failed', 'email', 'Email is alrealy used.')
    uid = next_id()
    sha1_passwd = '{}:{}'.format(uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image=Glo.get_avatar(hashlib.md5(email.encode('utf-8')).hexdigest()))
    await user.save()
    # make session cookie
    r = web.Response()
    r.set_cookie(Glo._COOKIE_NAME, Glo.user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '****'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


# 登录API
@post('/api/authenticate')
async def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]

    # check password
    uid_passwd = '{}:{}'.format(user.id, passwd)
    if user.passwd != hashlib.sha1(uid_passwd.encode('utf-8')).hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # 验证完成，set cookie
    r = web.Response()
    r.set_cookie(Glo._COOKIE_NAME, Glo.user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '****'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

# 注册
@get('/register')
async def register():
    return {
        '__template__': 'register.html'
    }

# 登录
@get('/signin')
def signin():
    return{
        '__template__': 'signin.html'
    }

# 退出
@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(Glo._COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    return r

# 文章列表
@get('/blogs')
async def blogs(*, page=1):
    page_index = Glo.get_page_index(page)
    num = await Blog.findNumber('count(id)')
    page = Page(num, page_index)
    if num == 0:
        blogs = []
    else:
        blogs = await Blog.findAll(orderBy='created_at desc', limit=(page.offset, page.limit))
    return {
        '__template__': 'blogs.html',
        'page': page,
        'blogs': blogs 
    }


# 文章详情
@get('/blog/{id}')
async def get_blog(id):
    blog = await Blog.find(id)
    comments = await Comment.findAll('id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = Glo.text2html(c.content)
    blog.html_content = mistune.markdown(blog.content, escape=False)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }


# 后台
@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    """ 创建文章 api """
    Glo.check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'blog name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(user_id=request.__user__.id, name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog


@get('/api/blog/{id}')
async def api_get_blog(*, id):
    """ 文章详情 api """
    blog = await Blog.find(id)
    return blog


@post('/api/blogs/{id}')
async def api_update_blog(id, request, *, name, summary, content):
    """ 编辑保存 api """
    Glo.check_admin(request)
    blog = await Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'blog name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog
    

@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
    """ 删除文章 api """
    Glo.check_admin(request)
    blog = await Blog.find(id)
    await blog.remove()
    return dict(id=id)


@get('/api/blogs')
async def api_blogs(*, page=1):
    """ 文章列表 api """
    page_index = Glo.get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)


@get('/manage/')
def manage():
    """ 重定向博客管理页面 """
    return 'redirect:/manage/blogs'

@get('/manage/blogs/create')
async def manage_create_blog():
    """ 写文章 """
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blogs'
    }


@get('/manage/blogs/edit')
async def manage_edit_blog(*, id):
    """ 编辑文章 """
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blogs/{}'.format(id)
    }


@get('/manage/blogs')
async def manage_blogs(*, page=1):
    """ 文章列表 """
    return {
        '__template__': 'manage_blogs.html',
        'page_index': Glo.get_page_index(page)
    }
