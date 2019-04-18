from orm.model import Utils
import datetime as dt



class C():
	def __getitem__(self,key):
		print(key)

c = C()
c[1:10]
