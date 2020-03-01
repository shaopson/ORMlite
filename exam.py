


class Optins():
    def __init__(self):
        self.cache = [1]


class Model(object):
    a = 1
    b = 2
    opts = Optins()



m = Model()
m2 = Model()
m2.opts.cache.append(2)
print(m.opts.cache)



