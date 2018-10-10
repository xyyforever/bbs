import time

from django.shortcuts import render
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin


def simple_middleware(get_response):
    def wrapper(request):
        print('------------------------------> process_request')
        response = get_response(request)
        print('------------------------------> process_response')
        return response
    return wrapper


class BlockMiddleware(MiddlewareMixin):
    '''
    根据用户访问频率阻塞用户访问的中间件, 每秒限制最大 3 次访问

        1. 1534231000.09
        ----------------------
        2. 1534231000.37
        3. 1534231000.72
        4. 1534231001.35
        ----------------------
        5. 1534231001.98
        ----------------------
        6. 1534231002.57
        7. 1534231003.22
    '''
    def process_request(self, request):
        user_ip = request.META['REMOTE_ADDR']
        block_user_key = 'BlockUser-%s' % user_ip    # 封禁用户的 key
        request_log_key = 'RequestLog-%s' % user_ip  # 用户访问历史 key

        # 首先检查当前用户 IP 是否被封禁
        if cache.get(block_user_key):
            print('user is blocked', user_ip)
            return render(request, 'blockers.html')

        # 检查用户访问频率
        now = time.time()
        t0, t1, t2 = cache.get(request_log_key, [0, 0, 0])  # 取出历史访问时间
        if (now - t0) < 1:
            print('set user as block user', user_ip)
            cache.set(block_user_key, 1, 86400)  # 将用户 IP 添加到缓存，并设置过期时间
            return render(request, 'blockers.html')
        else:
            print('update request log')
            cache.set(request_log_key, [t1, t2, now])
