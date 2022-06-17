import os
def mkdir(path):
    if os.path.exists(path):
        return
    os.makedirs(path)