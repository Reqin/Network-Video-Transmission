# --*-- coding:utf8 --*--
import numpy as np
import cv2
import time
import threading
import socket
from as_utils.utils import *

# 兼容python2和3的queue
import sys

if int(sys.version[0]) > 2:
    from queue import Queue
else:
    from Queue import Queue


def communicate(queue_frame, queue_received, queue_sock_server, address):
    '''

    :param queue_frame:
    :param queue_received:
    :param queue_sock_server:
    :param address:
    :return:
    '''
    while True:
        try:
            # 当程序执行到这一部时，有两种情况
            # 1.第一次建立连接
            # 2.建立的连接出错，socket将被销毁再重新建立
            # 当socket函数为空时，阻塞主动获取socket队列值的函数
            queue_sock_server.queue.clear()
            # 新建socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 连接
            sock.connect(address)
            # 将生效的socket送入队列，供receive函数使用
            queue_sock_server.put(sock)
        except socket.error as error:
            print(error)
            time.sleep(1)
            continue
        while True:
            # 发送数据
            # 在进行数据发送的时候，操作分为三部
            # 1.进行连接.服务端确认连接之后，将发送其建立连接的时间，接收它，这一步由其他线程函数完成，我们在这里读取服务时间信息队列以获取，如果读取服务时间信息队列不存在将阻塞
            # 2.发送下一次将要发送的主要数据的长度
            # 3.发送主要数据
            # 4.将接收到的服务建立时间返回做时间有效性校验
            # 接下来是具体的执行步骤
            # 从数据队列里面读取需要发送的值
            # 当数据队列为空时，阻塞到数据队列里面有值为止
            str_buf = queue_frame.get()
            # 获取主要数据的长度
            str_buf_length = buf_encode(len(str_buf), 32)
            try:
                # 1.读取服务时间信息以获取一次信息交换服务建立的时间
                when_conn_start = sock.recv(32)
                print(when_conn_start)
                # 2.发送主要数据段长度
                sock.send(str_buf_length)
                # 3.发送主要数据
                sock.send(str_buf)
                # 4.发送服务建立时间
                sock.send(when_conn_start)
                # 5.接收是否等待数据接收标示
                is_continue = int(sock.recv(1, socket.MSG_WAITALL))
                print(is_continue)
                if is_continue:
                    info = sock.recv(1024, socket.MSG_WAITALL)
                    queue_received.put(info)
            except socket.error as error:
                time.sleep(1)
                print(error)
                break


def process_received(queue_received_buf):
    while True:
        data = queue_received_buf.get()
        print('fps=', str(data))


def frame_to_queue(queue_frame_buf):
    # 开启摄像头
    handle = cv2.VideoCapture(0)
    while True:
        try:
            # 获取下一帧数据
            frame = next_frame(handle)
            # 编码数据
            frame_encoded = encode(frame)
            # 转换为numpy数组方便传输
            np_data = np.array(frame_encoded)
            # 转换为字符形式在网络中传输
            str_data = np_data.tostring()
            # 为了保证图像数据的实时性，清空图像数据队列并进行刷新
            # 清空图像数据队列
            queue_frame_buf.queue.clear()
            # 填入图像数据队列最新的数据
            queue_frame_buf.put(str_data)
        except cv2.error as error:
            print(120, error)


def thread_main():
    # 目标主机地址
    to_address = ('10.42.0.1', 1998)
    # 采集到的图像队列
    queue_frame = Queue(maxsize=1)
    # sock队列
    queue_sock = Queue(maxsize=1)
    # 收到的消息队列
    queue_received = Queue(maxsize=1)
    # 服务建立的时间
    queue_when_conn_start = Queue(maxsize=1)

    # 收集线程
    threads = []
    # 1.采集图像数据的子线程
    thread_frame_to_queue = threading.Thread(target=frame_to_queue, args=(queue_frame,))
    threads.append(thread_frame_to_queue)
    # 2.发送图像数据的子线程
    thread_communicate = threading.Thread(target=communicate,
                                          args=(queue_frame, queue_received, queue_sock, to_address))
    threads.append(thread_communicate)
    # 3.处理返回数据的子线程
    thread_receive_process = threading.Thread(target=process_received, args=(queue_received,))
    threads.append(thread_receive_process)

    # 开启全部线程
    for thread in threads:
        thread.start()


if __name__ == '__main__':
    thread_main()
