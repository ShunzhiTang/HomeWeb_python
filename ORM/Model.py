import uuid
from ORM.ORMHelper import Model,StringField,IntegerField,BooleanField,TextField,FloatField
import  asyncio,os,time

def next_id():
    # 生成长度为50的随记字符串
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = 'users'
    id = StringField(primary_key=True,default=next_id,ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    image  = StringField(ddl='varchar(50)')
    admin = BooleanField()
    create_at = FloatField(default=time.time())


class Blog(Model):
    

