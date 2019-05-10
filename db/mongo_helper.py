# -*- coding: utf-8 -*-
# @Time : 2019-01-28 15:33
# @Author : cxa
# @File : mongo_helper.py
# @Software: PyCharm
import pymongo
from YouMin.logger.log import storage,crawler
from YouMin.db import Config
# 数据库基本信息
db_configs = {
    'type': 'mongo',
    'host': '127.0.0.1',
    'port': '27017',
    "user": "",
    "password": "",
    'db_name': Config.DB_NAME
}

class Mongo():
    def __init__(self):
        self.col=Config.TABLE_NAME#数据库表名
        self.db_name = db_configs.get("db_name")
        self.host = db_configs.get("host")
        self.port = db_configs.get("port")
        self.client = pymongo.MongoClient(f'mongodb://{self.host}:{self.port}')
        self.username = db_configs.get("user")
        self.password = db_configs.get("passwd")
        if self.username and self.password:
            self.db = self.client[self.db_name].authenticate(self.username, self.password)
        self.db = self.client[self.db_name]

    def find_data(self):
        # 获取状态为0的数据
        data = self.db[self.col].find({"status": 0}, {"_id": 0})
        gen = (item for item in data)
        return gen

    def change_status(self, uuid, item, status_code=0):
        # status_code 0:初始,1:开始下载，2下载完了
        item["status"] = status_code
        self.db[self.col].update_one({'uuid': uuid}, {'$set': item})

    def save_data(self, items):
        if isinstance(items, list):
            for item in items:
                try:
                    self.db[self.col].update_one({
                        'uuid': item.get("uuid")},
                        {'$set': item},
                        upsert=True)
                except Exception as e:
                    storage.error(f"数据插入出错:{e.args},此时的item是:{item}")
        else:
            try:
                self.db[self.col].update_one({
                    'uuid': items.get("uuid")},
                    {'$set': items},
                    upsert=True)
            except Exception as e:
                storage.error(f"数据插入出错:{e.args},此时的item是:{item}")


if __name__ == '__main__':
    m = Mongo()
    m.find_data()
