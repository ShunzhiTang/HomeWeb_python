from iterable.error import APIError

__author__  = 'Michael Tang'
import  asyncio,os,functools,inspect,logging;logging.basicConfig(logging.INFO)
from  aiohttp import web
from urllib import parse

def get(path):
    '''
    装饰器 Define decorator @get('/path')
    :param path:
    :return:
    '''
    def decorator(func):
        # 函数装饰器
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return  decorator

def post(path):
    '''
    装饰器 Define decorator @post('/path')
    :param path:
    :return:
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator

# private method
# 获取必须参数数组
def get_required_kw_args(fn):
    args = []
    # 获取fn 参数名称与相应参数对象的有序映射。
    params = inspect.signature(fn).parameters
    for name ,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

# 获取参数名称
def get_named_kw_args(fn):
    args = []
    params = inspect.signature(fn).parameters
    for name , param in params.items():
        if param.kind  == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)

# KEYWORD_ONLY ：   值必须作为关键字参数提供。在*或* args之后出现
def has_named_kw_args(fn):
    params = inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True

# 没有绑定到任何其他参数的关键字参数的dict。这对应于Python函数定义中的一个** kwargs参数。
def has_var_kw_arg(fn):
    params = inspect.signature(fn).parameters
    for name ,param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return  True

# * args 对应 VAR_POSITIONAL
def has_request_arg(fn):
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name ,param in params.items():
        if name  == 'request':
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function: %s%s' % (fn.__name__, str(sig)))
    return found

# 定义RequestHandler
'''
RequestHandler目的就是从URL函数中分析其需要接收的参数，从request中获取必要的参数，
调用URL函数，然后把结果转换为web.Response对象，这样，就完全符合aiohttp框架的要求
'''
class RequestHandler(object):
    def __init__(self,app,fn):
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_arg(fn)
        self._has_var_kw_arg = has_var_kw_arg(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    # 异步协程
    # 定义了__call__()方法，因此可以将其实例视为函数。
    #可以通过在其类中定义__call __（）方法来调用任意类的实例。
    async def __call__(self, request):
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method == 'POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing Content-Type.')
                ct = request.content_type.lower()
                if ct.startswith('application/json'):
                    params =await request.json()
                    if not isinstance(params,dict):
                        return web.HTTPBadRequest('JSON body must be object.')
                    kw = params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported Content-Type: %s' % request.content_type)

            if request.method == 'GET':
                qs = request.query_string
                if qs:
                    kw = dict()
                    # parse 解析url
                    for k,v  in  parse.parse_qs(qs,True).items():
                        kw[k] = v[0]
        if kw is None:
            kw = dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                copy = dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name] = kw[name]
                kw = copy

            #check named arg
            for k , v in request.match_info.items():
                if k in kw:
                    logging.warning('Duplicate arg name in named arg and kw args: %s' % k)
                kw[k] = v
        if self._has_request_arg:
            kw['request'] = request
        # check required kw
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        logging.info('call with args : %s' % str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)

def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
    app.router.add_static('/static/',path)
    logging.info('add static %s => %s' % ('/static/',path))

def add_route(app,fn):
    # method is post or get
    method = getattr(fn,'__method__',None)
    path = getattr(fn,'__route__',None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined %s' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))
    app.router.add_route(method,path,RequestHandler(app,fn))

def add_routes(app,module_name):
    n = module_name.rfind('.')
    if n == (-1):
        mod = __import__(module_name,globals(),locals())
    else:
        name = module_name[n+1:]
        mod = getattr(__import__(module_name[:n],globals(), locals(), [name]), name)
    for attr  in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod,attr)
        #可调用
        if callable(fn):
            method = getattr(fn,'__method',None)
            path = getattr(fn,'__route__',None)
            if method and path:
                add_route(app,fn)






