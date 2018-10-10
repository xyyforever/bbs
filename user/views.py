from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password

from user.forms import RegisterForm
from user.models import User
from user.helper import get_access_token
from user.helper import get_user_show
from user.helper import login_required


def register(request):
    if request.method == 'POST':
        # 取出数据
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            # 密码加密处理
            user = form.save(commit=False)
            user.password = make_password(user.password)
            user.save()

            # 登陆、跳转
            request.session['uid'] = user.id
            request.session['nickname'] = user.nickname
            request.session['avatar'] = user.avatar
            return redirect('/user/info/')
        else:
            return render(request, 'register.html', {'error': form.errors})
    return render(request, 'register.html')


def login(request):
    if request.method == 'POST':
        nickname = request.POST.get('nickname')
        password = request.POST.get('password')
        try:
            user = User.objects.get(nickname=nickname)
        except User.DoesNotExist:
            return render(request, 'login.html',
                          {'error': '用户不存在', 'auth_url': settings.WB_AUTH_URL})

        if check_password(password, user.password):
            # 登陆、跳转
            request.session['uid'] = user.id
            request.session['nickname'] = user.nickname
            request.session['avatar'] = user.avatar
            return redirect('/user/info/')
        else:
            return render(request, 'login.html',
                          {'error': '密码错误', 'auth_url': settings.WB_AUTH_URL})
    return render(request, 'login.html', {'auth_url': settings.WB_AUTH_URL})


def logout(request):
    request.session.flush()  # 清理当前 session 数据
    return redirect('/user/login/')


@login_required
def user_info(request):
    uid = int(request.session.get('uid'))
    user = User.objects.get(pk=uid)
    return render(request, 'user_info.html', {'user': user})


def wb_callback(request):
    code = request.GET.get('code')

    # 获取 access token
    result = get_access_token(code)
    if 'error' in result:
        return render(request, 'login.html',
                      {'error': result['error'], 'auth_url': settings.WB_AUTH_URL})
    access_token = result['access_token']
    uid = result['uid']

    # 获取用户信息
    result = get_user_show(access_token, uid)
    if 'error' in result:
        return render(request, 'login.html',
                      {'error': result['error'], 'auth_url': settings.WB_AUTH_URL})
    screen_name = result['screen_name']
    avatar_url = result['avatar_hd']

    # 取出用户，如果不存在，自动注册
    user, created = User.objects.get_or_create(nickname=screen_name)
    if created:
        user.plt_icon = avatar_url
        user.save()

    # 登陆、跳转
    request.session['uid'] = user.id
    request.session['nickname'] = user.nickname
    request.session['avatar'] = user.avatar
    return redirect('/user/info/')
