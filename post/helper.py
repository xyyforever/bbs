from django.core.cache import cache

from common import rds
from post.models import Post


def page_cache(timeout):
    def deco(view_func):
        def wrapper(request):
            key = 'PageCache-%s-%s' % (request.session.session_key, request.get_full_path())
            # 先从缓存获取
            response = cache.get(key)
            # print('get from cache:', response)
            if response is None:
                # 缓存取不到，直接执行 view 函数，并将结果存入缓存
                response = view_func(request)
                # print('get from views:', response)
                cache.set(key, response, timeout)
                # print('set to cache')
            return response
        return wrapper
    return deco


def read_count(read_view):
    def wrapper(request):
        response = read_view(request)
        if response.status_code == 200:  # 检查状态码
            post_id = request.GET.get('post_id')
            rds.zincrby('ReadRank', post_id, 1)  # 文章阅读量 +1
        return response
    return wrapper


def get_top_n(num):
    '''获取阅读排行前 N 的数据'''
    # ori_data = [
    #     (b'31', 507.0),
    #     (b'2',   88.0),
    #     (b'34',  24.0),
    # ]
    ori_data = rds.zrevrange('ReadRank', 0, num - 1, withscores=True)  # 取出原始数据

    # rank_data = [
    #     [31, 507],
    #     [ 2,  88],
    #     [34,  24],
    # ]
    rank_data = [[int(post_id), int(count)] for post_id, count in ori_data]  # 清洗原始数据

    # 方法一：思路简单，效率低，性能差
    # for item in rank_data:
    #     post = Post.objects.get(pk=item[0])  # 替换每一项的第一个元素
    #     item[0] = post

    # 方法二
    # post_id_list = [post_id for post_id, _ in rank_data]  # 批量取出 id 列表
    # posts = Post.objects.filter(id__in=post_id_list)    # 批量获取 post
    # posts = sorted(posts, key=lambda post: post_id_list.index(post.id))  # 重新按阅读量排序
    # # 按位置逐一替换
    # for post, item in zip(posts, rank_data):
    #     item[0] = post

    # 方法三
    post_id_list = [post_id for post_id, _ in rank_data]  # 批量取出 id 列表
    # posts = {
    #     2: <Post: Post object>,
    #     3: <Post: Post object>,
    #     25: <Post: Post object>,
    # }
    posts = Post.objects.in_bulk(post_id_list)  # 批量获取 post
    # 按位置逐一替换
    for item in rank_data:
        item[0] = posts[item[0]]

    return rank_data
