from ormlite import fields,utils
from ormlite.model import Where
import datetime

d = {
	"a":1,
	"b__ge":'sdf',
	"c__in":('a','c','b'),
	"d__range":(1,2),
	"e__endswith":'shao',
	"d":datetime.datetime.today(),
	'sfds__lt':datetime.datetime.today()
}


a = Where(d)
b = Where('B')
c = Where("C")

a |= b
print(a.as_sql())


