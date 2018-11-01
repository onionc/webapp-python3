#!/usr/bin/python

import time, uuid
from orm import Model, StringField, BooleanField, IntegerField, FloatField, TextField

def next_id():
    return "{0:0<15d}{1}000".format(int(time.time() * 1000), uuid.uuid4().hex.upper())

class User(Model):
    """ 用户表 """
    __table__ = 'users'
    
    id = StringField(primary_key=True, default=next_id, ddl='varchar(64)')
    email = StringField(ddl='varchar(64)')
    passwd = StringField(ddl='varchar(64)')
    admin = BooleanField()
    name = StringField()
    image = StringField()
    created_at = FloatField(default=time.time)


class Blog(Model):
    """ 博客表 """
    __table__ = 'blogs'
   
    id = StringField(primary_key=True, default=next_id)
    user_id = StringField(ddl='varchar(64)')
    name = StringField()
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)


class Comment(Model):
    __table__ = 'comments'
    
    id = StringField(primary_key=True, default=next_id)
    user_id = StringField(ddl='varchar(64)')
    title = StringField('varchar(128)')
    content = TextField()
    created_at = FloatField(default=time.time)
