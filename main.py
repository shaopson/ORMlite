import sys
from test import Log,User

log = Log.object.get(id=1)
print(log.user)

log.user