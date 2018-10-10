from django.db import models

from user.models import User


class Post(models.Model):
    uid = models.IntegerField()
    title = models.CharField(max_length=64)
    created = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    @property
    def auth(self):
        if not hasattr(self, '_auth'):
            self._auth = User.objects.get(id=self.uid)
        return self._auth

    def comments(self):
        '''帖子对应的所有评论'''
        return Comment.objects.filter(post_id=self.id).order_by('-id')

    def tags(self):
        '''帖子拥有的所有 tag'''
        relations = PostTagRelation.objects.filter(post_id=self.id).only('tag_id')
        tag_id_list = [r.tag_id for r in relations]
        return Tag.objects.filter(id__in=tag_id_list)

    def update_tags(self, tag_names):
        '''更新帖子对应的 tag'''
        updated_tags = set(Tag.ensure_tags(tag_names))  # 确保传入的 tag 存在, 不存在的直接创建出来
        exist_tags = set(self.tags())                   # 当前帖子已存在的 tags

        # 处理需要新增关系
        new_tags = updated_tags - exist_tags                # 需要新构建关联的 tags
        need_create_tag_id_list = [t.id for t in new_tags]  # 待创建关联的 tag id 列表
        PostTagRelation.add_relations(self.id, need_create_tag_id_list)

        # 处理需要删除的关系
        old_tags = exist_tags - updated_tags                # 需要删除关联的 tags
        need_delete_tag_id_list = [t.id for t in old_tags]  # 带删除关联的 tag id 列表
        PostTagRelation.del_relations(self.id, need_delete_tag_id_list)


class Comment(models.Model):
    uid = models.IntegerField()
    post_id = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    @property
    def auth(self):
        '''评论的作者'''
        if not hasattr(self, '_auth'):
            self._auth = User.objects.get(id=self.uid)
        return self._auth

    @property
    def post(self):
        '''评论的帖子'''
        if not hasattr(self, '_post'):
            self._post = Post.objects.get(id=self.post_id)
        return self._post


class Tag(models.Model):
    name = models.CharField(max_length=16, unique=True)

    def posts(self):
        '''Tag 拥有的所有 Post'''
        relations = PostTagRelation.objects.filter(tag_id=self.id).only('post_id')
        post_id_list = [r.post_id for r in relations]
        return Post.objects.filter(id__in=post_id_list)

    @staticmethod
    def clean_str_tags(str_tags):
        return [s.strip()
                for s in str_tags.title().replace('，', ',').split(',')
                if s.strip()]

    @classmethod
    def ensure_tags(cls, tag_names):
        '''确保传入的 tag 存在'''
        exist_names = {t.name for t in cls.objects.filter(name__in=tag_names)}
        new_names = set(tag_names) - exist_names
        if new_names:
            new_tags = [cls(name=name) for name in new_names]
            cls.objects.bulk_create(new_tags)
        return cls.objects.filter(name__in=tag_names)


class PostTagRelation(models.Model):
    '''Post 与 Tag 的关系表'''
    post_id = models.IntegerField()
    tag_id = models.IntegerField()

    @classmethod
    def add_relations(cls, post_id, tag_id_list):
        '''批量建立 post 与 tag 的关联'''
        relations = [cls(post_id=post_id, tag_id=tid) for tid in tag_id_list]
        cls.objects.bulk_create(relations)

    @classmethod
    def del_relations(cls, post_id, tag_id_list):
        '''批量删除 post 与 tag 的关联'''
        cls.objects.filter(post_id=post_id, tag_id__in=tag_id_list).delete()
