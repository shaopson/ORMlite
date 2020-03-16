# ORMlite

一个简单的Python ORM,支持sqlite3 mysql, 具有延迟查询，链式查询等功能
接口模仿了Django的ORM框架 和Django ORM一样简单，易用，ORMlite不支持迁移功能(migrate)

### 快速上手
如果你使用过Django的ORM，那么你会感觉非常熟悉

创建model,使用sqlite3
```python
import ormlite
from ormlite import configuration
from ormlite.db.utils import create_tables

#设置数据库
configuration.conf_db({
    "ENGINE":"ormlite.db.sqlite3",
    "NAME":"db.sqlite3",
})
#开启Debug 查询时显示生成的sql语句
configuration.debug = True

#定义Model
class User(ormlite.Model):
    id = ormlite.PrimaryKey()
    name = ormlite.CharField(max_length=50)
    sex = ormlite.CharField(max_length=1)
    birthday = ormlite.DateField()

#创建
create_tables([User,],configuration.db)
```


创建对象

```python
import datetime
user = User(name='test',sex='M',birthday=datetime.datetime(2020,1,1).date())
user.save()
```

简单查询
```python
#返回单个User实例
user = User.object.get(id=1)

#获取全部User实例
users = User.object.all()

#查询所有id大于10的实例
# ge:>=,  gt:>, le:<=, lt:<
users = User.object.query(id__gt=10)

#排除所有id大于10的实例
users = User.object.exclude(id__gt=10)

#排序
users = User.object.all().sort('id')#正序
users = User.object.all().sort('-id')#反序

#切片
users = User.object.all()[2:4]
#第一个
user = User.object.all().first()
#最后一个
user = User.object.all().last()

#计数
count = User.object.all().count()

#只查询某个字段(结果以键值对的格式返回)
names = User.object.all().values('name')
#<Query [{'name': 'aa'}, {'name': 'bb'}, {'name': 'cc'}, {'name': 'dd'},...]>

#只查询某个字段(结果以列表的格式返回)
names = User.object.all().items('name')
#<Query [('aa',), ('bb',), ('cc',), ('dd',),...]>

#列表降维
names = User.object.all().items('name',flat=True)
#<Query ['aa', 'bb', 'cc', 'dd',]>

#数据聚合
from ormlite.query import Count,Min,Max,Sum,Avg
result = User.object.all().values(count=Count('id'))
#<Query [{'count': 10}]>

#分组计算
result = User.object.all().values(count=Count('name')).group('name')
#[{'name': 'aa', 'count': 1}, {'name': 'bb', 'count': 1}, {'name': 'cc', 'count': 1}]
```

###数据库配置
####sqlite3

```
from ormlite import configuration
configuration.conf_db({
    "ENGINE":"ormlite.db.sqlite3",
    "NAME":"db.sqlite3",
})
```

####mysql
当使用mysql时，需要安装mysql-connector

```
from ormlite import configuration
configuration.conf_db({
    "ENGINE":"ormlite.db.mysql",
    'NAME': 'ormlite',
    'USER': 'root',
    'PASSWORD': 'ormlite',
    'HOST': 'localhost',
    'PORT': '3306',
    'OPTIONS': {
        'autocommit': True,
    }
})
```

