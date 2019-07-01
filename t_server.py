# coding:utf8
import threading
import socket
import sys
import time
from modules.video.Processor import Processor
from modules.network.Communicator import Communicator

if int(sys.version[0]) > 2:
    from queue import Queue
else:
    from Queue import Queue


def communicate(communicator, frame):
    while True:
        # 1.为保证图像传输的实时性，每次通讯开始时清空图像帧队列
        # frame.queue.clear()
        # 1.发送超时验证用时间,编码长度为32
        communicator.set_message(time.time()).encode(32).send()
        # 2.获取主要数据长度
        current_frame_len = communicator.recv(32)
        # 3.获取主要数据
        current_frame = communicator.recv(int(current_frame_len))
        # 4.接收验证用时间
        v_time = communicator.recv(32)
        # 5.超时处理
        delay = time.time() - float(v_time)
        print('delay', delay)
        if delay > 0.08:
            communicator.set_message(0).encode(1).send()
        else:
            communicator.set_message(1).encode(1).send()
            frame.put(current_frame)
            communicator.set_message('ok').encode(1024).send()


def frame_process(frame, detector):
    while True:
        frame.queue.clear()
        current_frame = frame.get()
        current_frame = Processor.decode(current_frame)
        import cv2
        cv2.imshow('s', current_frame)
        cv2.waitKey(10)


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
            # 初始化通讯器
            communicator = Communicator(addr, conn)
            # 设置进程间通讯队列
            # 图片队列
            frame = Queue(maxsize=1)
            # 收集线程
            threads = [
                # 通讯线程
                threading.Thread(target=communicate, args=(communicator, frame,)),
                # 图像帧处理线程
                threading.Thread(target=frame_process, args=(frame, detector,)),
            ]
            # 启动子线程
            for thread in threads:
                thread.start()


if __name__ == '__main__':
    thread_main()
