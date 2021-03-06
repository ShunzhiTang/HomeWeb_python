# orm
__author__ = 'Michael Tang'

import logging;logging.basicConfig(level=logging.INFO)

import database.MysqlHelper

import asyncio,aiomysql


def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)

class Field(object):
    def __init__(self ,name , column_type,primary_key,default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return  '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

class ModelMetaclass(type):
    def __new__(cls, name,bases,attrs):
        #排除Model本身
        if name == 'Model':
            return type.__new__(cls ,name,bases,attrs)
        #获取table的名称
        tableName = attrs.get('__table__',None) or name
        logging.info('found model: %s (table: %s)' % (name, tableName))
        #获取所有的Field的主键名
        mappings = dict()
        fields = []
        primaryKey = None
        for k ,v in attrs.items():
            if isinstance(v ,Field):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise  RuntimeError('Primary key not found')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f:'`%s`' % f ,fields))
        attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey  # 主键属性名
        attrs['__fields__'] = fields  # 除主键外的属性名
        # 默认构造 select ，update ，insert，delete
        attrs['__select__'] = 'select `%s` ,%s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (
        tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
        tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return  type.__new__(cls,name,bases,attrs)


class Model(dict, metaclass=ModelMetaclass):
    def __init__(self , **kw):
        super(Model,self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return  self[key]
        except KeyError:
            raise ArithmeticError(r"'Model' object has no attribute %s" ,key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self,key):
        return getattr(self,key,None)

    def getValueOrDefault(self,key):
        value = getattr(self,key,None)
        if value is None:
            field = self.__mappings__[key]
            if field.defalut is not None:
                value = field.defalut() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self,key,value)
        return value

    @classmethod
    @asyncio.coroutine
    async def find(cls,pk):
        rs = await  database.MysqlHelper.select('%s  where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return  None
        return cls(**rs[0])

    @classmethod
    @asyncio.coroutine
        #**kw 可变的键值对
    async def findAll(cls,where = None ,args = None,**kw):
        'find objects by where clause'
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy',None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit',None)
        if limit is not  None:
            sql.append('limit')
            if isinstance(limit ,int):
                sql.append('?')
                sql.append(limit)
            elif isinstance(limit,tuple) and len(limit) == 2:
                sql.append('?,?')
                sql.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await database.MysqlHelper.select(' '.join(sql), args)
        return [cls(**r) for  r in rs]

    @classmethod
    async def findNumber(cls,selectField,where=None, args=None):
        'find number by select and where'
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await database.MysqlHelper.select(' '.join(sql),args,1)
        if len(rs) == 0 :
            return None
        return rs[0]['_num_']
    async def  save(self):
        args = list(map(self.getValueOrDefault,self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await database.MysqlHelper.execute(self.__insert__,args)

        if rows != 1:
            logging.warn('failed to insert record : affected rows')
        else:
            logging.info('insert successed')

    async def update(self):
        #获取除主键外的属性名
        args = list(map(self.getValue,self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await database.MysqlHelper.execute(self.__update__,args)
        if rows != 1:
            logging.warn('failed to update record : affected rows')

    async def  remove(self):
        # 获取主键
        args = [self.getValue(self.__primary_key__)]
        rows = await database.MysqlHelper.execute(self.__delete__,args)
        if rows != 1:
            logging.warn('failed to delete record : affected rows')

# 映射 varchar 的 StringField

class StringField(Field):
    def __init__(self,name = None ,primary_key = False,default=None, ddl='varchar(100)'):
        super().__init__(name,ddl,primary_key,default)

class BooleanField(Field):
    def __init__(self,name = None,default = False):
        super().__init__(name,'boolean',False,default)

class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)

class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)
