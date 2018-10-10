import requests
from django.conf import settings
from django.shortcuts import render, redirect

from user.models import User
from user.models import Permission


def get_access_token(code):
    '''获取微博 access_token'''
    args = settings.WB_ACCESS_TOKEN_ARGS.copy()  # 以 settings 配置为原型得到一个副本
    args['code'] = code
    resp = requests.post(settings.WB_ACCESS_TOKEN_API, data=args)  # 访问微博 token 接口
    if resp.status_code == 200:
        return resp.json()
    else:
        return {'error': '微博访问出错'}


def get_user_show(access_token, uid):
    '''获取微博用户信息'''
    args = settings.WB_USER_SHOW_ARGS.copy()
    args['access_token'] = access_token
    args['uid'] = uid
    resp = requests.get(settings.WB_USER_SHOW_API, params=args)  # 访问微博 user_show 接口
    if resp.status_code == 200:
        return resp.json()
    else:
        return {'error': '微博访问出错'}


def login_required(view_func):
    '''检查用户是否登陆'''
    def wrapper(request):
        if request.session.get('uid'):
            return view_func(request)
        else:
            return redirect('/user/login/')
    return wrapper


def check_perm(perm_name):
    def deco(view_func):
        def wrapper(request):
            # 取出当前用户
            uid = request.session['uid']
            user = User.objects.get(id=uid)

            # 检查用户权限
            if user.has_perm(perm_name):
                return view_func(request)
            else:
                return render(request, 'blockers.html')
        return wrapper
    return deco
