import joblib
from threading import Thread, Lock, RLock, Semaphore


class KeyValue:    #键值存储
    def __init__(self, path=None):
        if path is None:
            self.db = {}         #数据库，字典
            self.path = None     #路径
        else:
            self.path = path
            self.db = joblib.load(path)     #已有存储

    def get(self, key):                       #取数据
        if self.db.__contains__(key):
            return "GET: Success.", self.db[key]
        else:
            return "GET: The key does not exist.", -1

    def put(self, key, value):        #存数据
        self.db.update({key: value})
        return "PUT: Success."

    def delete(self, key):     #删数据
        if self.db.__contains__(key):
            del self.db[key]
            return "DELETE: Success."
        else:
            return "DELETE: The key does not exist."

    def save(self, path=None):        #保存到本地
        if path is None:
            if self.path is not None:
                joblib.dump(self.db, self.path)
                return "SAVE: Success."
            else:
                return "SAVE: Failed, please set the path to save."
        else:
            joblib.dump(self.db, path)
            return "SAVE: Success."

    def show(self):          #返回数据
        return self.db

    def clear(self):        #清除数据
        self.db.clear()
