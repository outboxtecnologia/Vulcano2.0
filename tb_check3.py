import os
base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath('backend/core/agents/tools.py'))))
print(os.path.join(base, "poc_database.sqlite"))
