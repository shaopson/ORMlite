




class C():

	def __reduce__(self,other):
		print("__reduce__")

	def __add__(self,other):
		print("__add__")

c = C()
