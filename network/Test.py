import ORM.ORMHelper
from ORM.Model import User,Blog,Comment
import database.MysqlHelper
import asyncio

async def test(loop):
    await database.MysqlHelper.create_pool(loop = loop,user='root',password='8888',database='homePage')

    user = User(name ='tang',email='kkkk@gmail.com', passwd = '111',image = 'wwww.iii.png',admin=False,id= '4',created_at='323113123190090')

    await  user.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()
# loop.close()
