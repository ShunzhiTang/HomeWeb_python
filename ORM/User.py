from ORM.ORMHelper import Model,StringField,IntegerField
import  asyncio
# from ORM.ORMHelper import Model,ModelMetaclass,StringField
class User(Model):
    __table__ = 'users'
    id = IntegerField(primary_key=True)
    name = StringField()

    @asyncio.coroutine
    def insert(self):
        print('insert xxx')
        yield from self.save()
        print('insert successed')

    def demo(self):
        return 'demo'

user = User(id = 123 ,name = 'Michael')
inscc =  user.insert()

print(next(inscc))


print(user.id,user.name)