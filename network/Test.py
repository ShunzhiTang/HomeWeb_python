import ORM.ORMHelper
from ORM.Model import User, Blog, Comment, next_id
import database.MysqlHelper
import asyncio,time,random


async def test(loop):
    await database.MysqlHelper.create_pool(loop = loop,user='www-data',password='www-data',database='homePage')
    emailStr = '%s@gamil.com' % random.randint(0,1000000)
    userID = next_id()
    userName = 'tangF'
    userImage = 'www.person.png'

    user = User(name =userName,email= emailStr, passwd = '111',image = userImage,admin=False,id=userID ,created_at=time.time())
    # blog = Blog(name='新浪微博', user_id= userID , user_name= userName, user_image= userImage, id=next_id(),
    #             created_at=time.time(),summary='我是一个注释',content='天气好啊')
    #
    # insert user table
    await  user.save()
    # await  blog.save()
    #select table
    blog =  await Blog.find('0015096735833925892090c774a4f108fe149f95bbef726000')
    print(blog.id , blog.user_name)



loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
# loop.run_forever()
# loop.close()
