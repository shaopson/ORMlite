

class Dec():
	def __init__(self,name):
		self.name = name


	def __get__(self,obj,cls):
		print('get')
		return obj.__dict__[self.name]

	def __set__(self,obj,value):
		print('set')
		obj.__dict__[self.name] = value

	def __delete__(self,obj):
		print('delete')
		del obj.__dict__[self.name]

class Test():
	d = Dec('d')

	def __init__(self,name):
		self.d = name

t = Test(22)
t.d = 1
print(t.d)
