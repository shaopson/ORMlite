


a = {
	"id":
		{
		'b':'00',
	    "name": "id",
	    "default": None,
	    "unique": False,
	    "null": True,
	    "column_type": "INTEGER"
  		}
  	}
	
b =	{
	"id":
		{
	    "name": "id",
	    "default": None,
	    "unique": True,
	    "null": True,
	    "column_type": "INTEGER",
	    'a':'tet'
  		}
  	}

def dict_compara(dict1,dict2):
	add = {}
	delete = {}
	modify = {}
	for key in dict1.keys() | dict2.keys():
		try:
			value1 = dict1[key]
		except KeyError:
			add[key] = dict2[key]
			continue
		try:
			value2 = dict2[key]
		except KeyError:
			delete[key] = dict1[key]
			continue
		if value1 != value2:
			if isinstance(value1,dict) and isinstance(value2,dict):
				modify[key] = dict_compara(value1,value2)
				continue
			modify[key] = (dict1[key],dict2[key])
	return {
		'add':add,
		'delete':delete,
		'modify':modify,
	}

r = dict_compara(a,b)
print(r)








