# coding:utf8

import argparse
import threading
import sys
from modules.video.Processor import Processor
from modules.network.Communicator import Communicator

if int(sys.version[0]) > 2:
    from queue import Queue
else:
    from Queue import Queue


def communicate(communicator, message_send, message_recv):
    while True:
        # 1.获取此次通讯服务端开始时间
        time_start = communicator.recv(32)
        print('time', time_start)
        # 2.获取此次通讯主要数据
        message = message_send.get()
        # 3.编码此次需要发送的数据长度
        message_len = len(message)
        # 4.发送数据长度
        communicator.set_message(message_len).encode(32).send()
        # 5.发送主要数据
        communicator.set_message(message).send()
        # 6.发送服务建立时间，用于服务端超时验证
        communicator.set_message(time_start).send()
        # 7.接收服务端消息,是否有后续消息
        flag = communicator.recv(1)
        print('flag', flag, )
        if flag == b'1':
            message = communicator.recv(1024)
            print('message',message)
            message_recv.put(message)


def get_frame(frame_processor, frame):
    while True:
        current_frame = frame_processor.next_frame().encode().frame
        frame.queue.clear()
        frame.put(current_frame)


def process_received(message_received):
    while True:
        message = message_received.get()
        print(message)


def main(arg):
    # 使用队列进行信息交互和线程控制
    # 通讯队列
    # 收到的消息
    message_received = Queue(maxsize=1)
    # 发送的消息
    # 图像帧队列
    frame = Queue(maxsize=1)

    # 初始化
    # 通讯器
    address = tuple([arg.address.split(':')[0], int(arg.address.split(':')[1])])
    communicator = Communicator(address=address)
    # 图像帧处理器
    frame_processor = Processor(source=arg.source)

    threads = [
        # 采集图像数据子线程
        threading.Thread(target=get_frame, args=(frame_processor, frame,)),
        # 通讯子线程
        threading.Thread(target=communicate, args=(communicator, frame, message_received,)),
        # 处理返回数据子线程
        threading.Thread(target=process_received, args=(message_received,))
    ]

    for thread in threads:
        thread.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', default='0.0.0.0:1998',
                        help='This address is used for communication between client and server.')
    parser.add_argument('--source', help='Image resources')
    args = parser.parse_args()
    main(args)
    pass
