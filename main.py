




def f(model=None,**kw):
	print(kw)
	print(model)

f(**{"a":1,"b":2},model='dfdf')
