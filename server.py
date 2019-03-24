# --*-- coding:utf8 --*--
import threading
import socket
import time
import cv2
import sys
import numpy as np
from as_utils.utils import *

# 兼容python2和3的queue
import sys

if int(sys.version[0]) > 2:
    from queue import Queue
else:
    from Queue import Queue


def communicate(queue_conn, queue_img):
    # 从队列中取得连接
    sock = queue_conn.get()
    while True:
        # 为了保证图像数据的实时性，每一次循环一开始都将清空图像数据队列
        queue_img.queue.clear()
        # 在服务端和用户端通信时，通信顺序如下
        # 1.发送服务建立时间
        # 2.接收用户要发送的主要数据的长度信息数据，这条数据的长度为1024
        # 3.接收用户要发送的主要数据
        # 4.接收服务建立时间
        # 开始
        try:
            # 1.发送服务建立时间,编码长度为1024
            when_conn_start = time.time()
            when_conn_start = buf_encode(when_conn_start, 32)
            sock.send(when_conn_start)
            # 2.接收用户发送的主要数据长度数据
            # length = collect_buf(sock, 32)
            length = sock.recv(32, socket.MSG_WAITALL)
            length = int(length)
            # 3.接收用户发送的主要数据
            # data_main_buf = collect_buf(sock, length)
            data_main_buf = sock.recv(length, socket.MSG_WAITALL)
            # 4.接收第一步发送的服务建立时间
            when_conn_start = sock.recv(32, socket.MSG_WAITALL)
            # 判断信息是否超时，若超时则丢弃重新接收,如果
            when_start = float(when_conn_start)
            now = time.time()
            delay = abs(now - when_start)
            print('lag', delay)
            if delay > 0.08:
                is_response = buf_encode(0, 1)
                sock.send(is_response)
                print('timeout')
            else:
                is_response = buf_encode(1, 1)
                sock.send(is_response)
                # 解码为numpy数组
                data_decoded = np.frombuffer(data_main_buf, np.uint8)
                # 解码解压缩
                img_decoded = cv2.imdecode(data_decoded, cv2.IMREAD_COLOR)
                # 将图片数据送入队列
                queue_img.put(img_decoded)
                # 为了防止图片数据没有即使被读取就被销毁，添加一个极小的时延
                time.sleep(0.0001)
                response = buf_encode('received and not delay', 1024)
                sock.send(response)
        except ValueError as e:
            print(e)
            continue


def img_process(queue_img, detector, queue_responce):
    while True:
        now = time.time()
        try:
            # 从队列中读取图片
            img = queue_img.get()
            print('img_lag', time.time() - now)
            cv2.imshow('now', img)
            cv2.waitKey(10)
            continue
            # 处理图片、识别
            image_processed, boxes, scores, labels = detector.detect(img)
            cv2.imshow('processed', image_processed)
            cv2.waitKey(10)
        except cv2.error as e:
            sock, addr = sock.accept()
            print(e)


def thread_main():
    # 监听地址
    address = ('0.0.0.0', 1998)
    #
    detector = None
    while True:
        # 建立TCP/IP套接字
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(address)
        # 最大挂起数量
        sock.listen(5)
        while True:
            # 接受请求
            conn, addr = sock.accept()
            # 设置进程间通讯队列
            # 图片队列
            queue_img = Queue(maxsize=1)
            # 连接队列
            queue_conn = Queue(maxsize=1)
            # 响应消息队列
            queue_response = Queue(maxsize=1)
            # 将成功建立的连接放入连接队列中
            queue_conn.put(conn)

            # 收集线程
            threads = []
            # 开启数据交换线程
            thread_communicate = threading.Thread(target=communicate, args=(queue_conn, queue_img))
            threads.append(thread_communicate)
            # 开启图片队列处理线程
            thread_img_process = threading.Thread(target=img_process,
                                                  args=(queue_img, detector, queue_response))
            threads.append(thread_img_process)

            # 启动子线程
            for thread in threads:
                thread.start()


if __name__ == '__main__':
    thread_main()
