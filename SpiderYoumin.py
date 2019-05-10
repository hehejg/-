# encoding: utf-8
"""
@author: He
@file: SpiderYoumin.py
@time: 2019/5/3/0003 上午 08:27
"""
import datetime
import hashlib

import requests
from lxml import etree

from YouMin.db.mongo_helper import Mongo
from YouMin.logger.log import crawler


class SpiderYoumin:
    def __init__(self):
        self.start_url = 'https://www.gamersky.com/'
        self.headers = {
            "Host": "www.gamersky.com",
            "Referer": "https://www.google.com.hk/",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "max-age=0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/69.0.3497.100 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

    def get_req(self, url):
        req = self.session.get(url)
        req.encoding = 'utf-8'
        return etree.HTML(req.text)

    def get_imgurl(self, req):
        # for xp in ['//ul[@class="Mid7img block"]/li','//ul[@class="Mid7img none"]/li']:
        datas = req.xpath('//ul[@class="Mid7img block"]/li')
        for data in datas:
            title = data.xpath('a/@title')[0]
            if not 'https://www.gamersky.com' in data.xpath('a/@href')[0]:
                href = 'https://www.gamersky.com' + data.xpath('a/@href')[0]
            else:
                href = data.xpath('a/@href')[0]
            self.save_data(title, href)

    def save_data(self, title, url):
        req = self.get_req(url)
        datas = req.xpath('//p[@align="center"]/img')  # a img
        tasks = []
        for data in datas:
            dic = {}
            dic['img_url'] = data.xpath('@src')[0]  # href src
            dic['title'] = title
            dic['name'] = dic['img_url'].split('/')[-1]
            dic['uuid'] = hashlib.md5(dic['name'].encode("utf-8")).hexdigest()
            dic['status'] = 0
            dic['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
            tasks.append(dic)
        Mongo().save_data(tasks)
        crawler.info(f'保存了{len(tasks)}到数据库中')
        req = self.get_req(url)
        for data in req.xpath('//div[@class="page_css"]/a'):
            next_page = data.xpath('text()')[0]
            if next_page == '下一页':
                self.save_data(title, data.xpath('@href')[0])

    def run(self):
        req = self.get_req(self.start_url)
        self.get_imgurl(req)


if __name__ == '__main__':
    YM = SpiderYoumin()
    YM.run()
