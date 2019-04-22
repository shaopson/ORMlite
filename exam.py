
class Database(object):

	def __init__(self,db):
		self.db = db

	def __enter__(self):
		print('enter')
		return 'sss'

	def __exit__(self,exc_type,exc_instance,traceback):
		print('exit')
		print('1',exc_type)
		print('2',exc_instance)
		print('3',traceback)

d = Database('1')

with d as a:
	raise KeyError('fdf')
	pass
