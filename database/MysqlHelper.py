
# 编写ORM
# 异步编程的一个原则：一旦决定使用异步，则系统每一层都必须是异步
# aiomysql 为mysql数据库提供了异步IO的驱动

# 1、创建连接池
# 创建一个全局的连接池，每个HTTP请求都可以从连接池中直接获取数据库连接

import logging; logging.basicConfig(level=logging.INFO)
import  asyncio ,aiomysql
from  aiohttp import  web

@asyncio.coroutine
def create_pool(loop ,**kw):
    logging.info('create database connection pool ...')
    print('-----xxxxx %s'% kw['database'])
    global  __pool
    __pool = yield from aiomysql.create_pool(
        # 数据库地址 端口  用户名 密码  数据库名 编码方式
        host = kw.get('host','localhost'),
        port = kw.get('port',3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['database'],
        charset = kw.get('charset' , 'utf8'),
        autocommit = kw.get('autocommit',True),
        maxsize = kw.get('maxsize',10),
        minsize = kw.get('minsize',1),
        loop = loop
    )


# select 语句
import  syslog
# size  获取多少条数据 如果传入size参数，就通过fetchmany()获取最多指定数量的记录，否则，通过fetchall()获取所有记录。
@asyncio.coroutine
def select(sql,args,size = None):
    logging.info(sql, args)
    global __pool
    with (yield from  __pool) as  conn:
        cur = yield  from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace('?', '%s'),args or ())
        if size:
            rs = yield  from cur.fetchmany(size)
        else:
            rs = yield  from cur.fetchall()
        yield  from cur.close()
        logging.info('Rows returned : %s' % len(rs))
        return rs


# insert  update  delete  需要的参数一样，所以使用execute函数实现

@asyncio.coroutine
def execute(sql ,args):
    logging.info(sql,args)
    with (yield from __pool) as conn:
        try:
            cur = yield  from conn.cursor()
            yield  from cur.execute(sql.replace('?' ,'%s'),args)
            affected = cur.rowcount
            yield  from  cur.close()
        except BaseException as e:
            raise
        return  affected