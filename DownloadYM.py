# encoding: utf-8
"""
@author: He
@file: Download.py
@time: 2019/5/2/0002 下午 09:16
"""
import asyncio
import concurrent
import os

import aiofiles
import aiohttp
import async_timeout
from aiostream import stream

from YouMin.db.motor_helper import MotorBase
from YouMin.logger.log import crawler, storage


async def get_img(item, buff):
    uuid = item.get("uuid")
    image_path = item.get("image_path")
    async with aiofiles.open(image_path, 'wb') as f:
        await f.write(buff)
        if os.path.exists(image_path):
            storage.info(f'成功下载图片{image_path}')
            await MotorBase().change_status(uuid, 1)  # 下载成功
        else:
            storage.info(f'下载图片失败{image_path}')
            await MotorBase().change_status(uuid, 0)  # 下载失败


async def get_buff(item, session)->None:
    uuid = item.get("uuid")
    # 题目层目录是否存在
    file_path = item.get("file_path")
    image_path = item.get("image_path")
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    # 文件是否存在
    if not os.path.exists(image_path):
        url = item.get("img_url").split('?')[-1]
        with async_timeout.timeout(60):  # 超时处理 60 秒
            try:
                async with session.get(url) as r:
                    if r.status == 200:
                        buff = await r.read()
                        if len(buff):
                            await get_img(item, buff)
            except Exception as e:
                # storage.error(image_path)
                storage.error(f'图片下载失败url为{url}错误为{e}')
    else:
        crawler.info(f'图片已经存在,路径为{image_path}')
        await MotorBase().change_status(uuid, 1)  # 下载成功


async def bound_fetch(item, session):
    """
    分别处理图片和内容的下载
    :param item:
    :param session:
    :return:
    """
    # md5name = item.get("md5name")
    file_path = r'E:\游民囧图'  # 设置文件保存路径
    file_path = os.path.join(file_path, item.get('title').strip())
    image_path = os.path.join(file_path, item.get('name'))  # 设置图片保存路径
    item["image_path"] = image_path
    item["file_path"] = file_path
    await get_buff(item, session)


async def branch(coros, limit=3):
    """
    使用aiostream模块对异步生成器做一个切片操作。limit为并发量
    :param coros: 异步生成器
    :param limit: 并发次数
    :return:
    """
    index = 0
    while True:
        xs = stream.preserve(coros)
        ys = xs[index:index + limit]
        t = await stream.list(ys)
        if not t:
            break
        await asyncio.ensure_future(asyncio.wait(t))
        index += limit + 1


async def run():
    """
    入口函数
    :return:
    """
    data = await MotorBase().find()
    crawler.info("开始下载图片")
    async with aiohttp.connector.TCPConnector(limit=300, force_close=True, enable_cleanup_closed=True) as tc:
        async with aiohttp.ClientSession(connector=tc) as session:
            coros = (asyncio.ensure_future(bound_fetch(item, session)) async for item in data)
            await branch(coros)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(5)
    loop.set_default_executor(executor)
    loop.run_until_complete(run())
    executor.shutdown(wait=True)
    loop.close()
