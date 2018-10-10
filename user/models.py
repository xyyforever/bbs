r'''
权限关系模型

User
    \
    UserRoleRelation
    /
Role
    \
    RolePermRelation
    /
Permission


权限分配
    admin    del_post
    admin    del_comment
    admin    del_user

    manager  add_post
    manager  del_post
    manager  add_comment
    manager  del_comment

    user     add_post
    user     add_comment
'''

from django.db import models


class User(models.Model):
    SEX = (
        ('M', '男'),
        ('F', '女'),
        ('S', '保密'),
    )

    nickname = models.CharField(max_length=16, unique=True)
    password = models.CharField(max_length=128)
    icon = models.ImageField()
    plt_icon = models.CharField(max_length=256)  # 第三方平台的头像地址
    age = models.IntegerField(default=18)
    sex = models.CharField(max_length=8, choices=SEX)

    @property
    def avatar(self):
        '''统一的用户头像 url'''
        return self.icon.url if self.icon else self.plt_icon

    def roles(self):
        '''用户拥有的所有角色'''
        relations = UserRoleRelation.objects.filter(uid=self.id).only('role_id')
        role_id_list = [r.role_id for r in relations]
        return Role.objects.filter(id__in=role_id_list)

    def has_perm(self, perm_name):
        '''检查用户是否具有某个权限'''
        for role in self.roles():
            for self_perm in role.permissions():
                if self_perm.name == perm_name:
                    return True
        return False


class UserRoleRelation(models.Model):
    uid = models.IntegerField()
    role_id = models.IntegerField()

    @classmethod
    def add_relation(cls, uid, role_id):
        '''添加一个用户和角色的关系'''
        relation, _ = cls.objects.get_or_create(uid=uid, role_id=role_id)
        return relation

    @classmethod
    def del_relation(cls, uid, role_id):
        '''删除一条用户和角色的关系'''
        cls.objects.get(uid=uid, role_id=role_id).delete()


class Role(models.Model):
    '''
    角色表

        admin   超级管理员
        manager 版主
        user    普通用户
    '''
    name = models.CharField(max_length=16, unique=True)

    def permissions(self):
        '''角色拥有的所有权限'''
        relations = RolePermRelation.objects.filter(role_id=self.id).only('perm_id')
        perm_id_list = [r.perm_id for r in relations]
        return Permission.objects.filter(id__in=perm_id_list)


class RolePermRelation(models.Model):
    role_id = models.IntegerField()
    perm_id = models.IntegerField()

    @classmethod
    def add_relation(cls, role_id, perm_id):
        '''添加一个角色和权限的关系'''
        relation, _ = cls.objects.get_or_create(role_id=role_id, perm_id=perm_id)
        return relation

    @classmethod
    def del_relation(cls, role_id, perm_id):
        '''删除一条角色和权限的关系'''
        cls.objects.get(role_id=role_id, perm_id=perm_id).delete()


class Permission(models.Model):
    '''
    权限表

        add_post    添加帖子
        add_comment 添加评论
        del_post    删除帖子
        del_comment 删除评论
        del_user    删除用户
    '''
    name = models.CharField(max_length=16, unique=True)
