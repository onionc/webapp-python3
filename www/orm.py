#!/usr/bin/python
# -*- coding:utf-8 -*-

__origin_author__ = 'Michael Liao'
import pdb
import asyncio
import aiomysql
import datetime
from functions import logger

def log(sql, args=()):
    logger.info('{0}\n\tsql: {1}\n\t args: {2}\n'.format(datetime.datetime.now(), sql, args))

async def create_pool(loop, **kw):
    """ 创建连接池 """
    logger.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host = kw.get('host', 'localhost'),
        port = kw.get('post', 3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['db'],
        charset = kw.get('charset', 'utf8'),
        autocommit = kw.get('autocommit', True),
        maxsize = kw.get('maxsize', 10),
        minsize = kw.get('minsize', 1),
        loop = loop
    )

async def select(sql, args, size=None):
    """ 查询 """
    log(sql, args)
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql.replace('?', '%s'), args or ())
            if size:
                rs = await cur.fetchmany(size)
            else:
                rs = await cur.fetchall()
        logger.debug('rows returned: {}'.format(len(rs)))
        return rs

async def execute(sql, args, autocommit=True):
    """ 执行SQL :param autocommit-自动提交，不自动提交则使用事务 """
    log(sql, args)
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                logger.debug(sql)
                logger.debug(args)
                await cur.execute(sql.replace('?', '%s'), args)
                affected = cur.rowcount
            if not autocommit:
                await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
        return affected

def create_args_string(num):
    """ 创建参数字符串 """
    L = []
    for n in range(num):
        L.append('?')
    return ','.join(L)
            

class Field(object):
    """ 字段类，保存字段名和字段类型 """
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        """ 字段描述 """
        return "<{0}, {1}:{2}>".format(self.__class__.__name__, self.column_type, self.name)


class StringField(Field):
    """ 字符串类型 """
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)

class BooleanField(Field):
    """ 布尔类型 """
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field):
    """ 整数类型 """
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
    """ 浮点类型 """
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)

class TextField(Field):
    """ 文本类型 """
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)


class ModelMetaClass(type):
    """ 定义元类 """
    def __new__(cls, name, bases, attrs):
        logger.debug('{} into metaclass ,yeeeeeeeeee '.format(name))
        # 排除Model类自身
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)

        # get table name
        tableName = attrs.get('__table__', None) or name
        logger.debug('found model:{0} (table: {1})'.format(name,tableName))
        
        # 找到所有的字段和主键
        mappings = {}
        fields = []
        primaryKey = None
        for k,v in attrs.items():
            logger.debug('found mapping: {0}=>{1}'.format(k,v))
            if isinstance(v, Field):
                mappings[k] = v
                if v.primary_key:
                    # finded primary_key
                    if primaryKey:
                        raise BaseException('Duplicate primary key for field:{}'.format(k))
                    primaryKey = k 
                else:
                    fields.append(k) # 非主键字段
        logger.debug("fields:{0}, pk{1}".format(str(fields), primaryKey))
        if not primaryKey:
            raise BaseException('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: "`{}`".format(f), fields)) # 非主键字段加``
        attrs['__mappings__'] = mappings # save field and column mapping
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields # 除主键外的属性名
        # 构造默认 select, insert, update and delete 语句
        attrs['__select__'] = "SELECT `{0}`, {1} FROM `{2}`".format(primaryKey, ','.join(escaped_fields), tableName)
        attrs['__insert__'] = "INSERT INTO `{0}` ({1}, `{2}`) VALUES ({3})".format(tableName, ','.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = "UPDATE `{0}` SET {1} WHERE `{2}`=?".format(tableName, ','.join(map(lambda f: "`{}`=?".format(mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = "DELETE FROM `{0}` where `{1}`=?".format(tableName, primaryKey)
        
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaClass):
    """ 模型基类 """
    def __init__(self, **kw):
        # logger.info('kw'+str(kw))        
        super().__init__(**kw)
        # logger.info(self)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '{}'".format(key))

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        """ 获取值 """
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        """ 获取值或者默认值 """
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logger.debug("using default value for {0}: {1}".format(key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    async def findAll(cls, where=None, args=None, **kw):
        """ find objects by where clause. """
        sql = [cls.__select__]

        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []

        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)

        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit)==2 :
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: {}'.format(str(limit)))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]

    @classmethod
    async def findNumber(cls, select_field, where=None, args=None):
        """ 查找条数 """
        sql = ['select {0} as _num from `{1}`'.format(select_field, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num']

    @classmethod
    async def find(cls, pk):
        """ find object by primary key """
        rs = await select("{0} where `{1}`=?".format(cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        """ 保存 """
        # pdb.set_trace()
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        logger.debug(" insert args:{}".format(args))
        if rows != 1:
            logger.info('failed to insert record : affected rows:{}'.format(rows))
       
    async def update(self):
        """ 更新 """ 
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        logger.debug(" update args:{}, sql:{}".format(args, self.__update__))
        if rows != 1:
            logger.info('failed to update by primary key: affected rows:{}'.format(rows))
    
    async def remove(self):
        """ 删除 """
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logger.info('failed to remove by primary key : affected rows:{}'.format(rows))
