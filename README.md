---
title: Python中的socket编程
tags: Python,socket,图像同传
grammar_cjkRuby: true
---


# 简介
本文介绍Python下的socket包的简单使用。Python下的socket包是一个低级的网络通讯包，包含TCP/IP协议通讯、UDP协议通讯、集群通讯等各种通讯接口。我主要用TCP/IP通讯制作了视频同传的一个小demo。
* 注意
**案例基于对TCP/IP协议的完全信任。**
这里是[实例代码的github地址](https://github.com/Reqin/Network-Video-Transmission)

# 建立一个socket连接
在多机通讯的时候，当我们去建立一个连接，我们需要让客户端去针对某一个主机的某个端口发起连接请求，此时如果服务端在监听端口，那么就可以进行连接、通讯等操作。在进行连接通讯的时候，我们可以选择TCP/IP、UDP等通讯协议，用户端和服务端的协议必须一致（这个用脚趾头都能想通吧）。
* 用户端发起请求
	```python?linenums
	# 目标主机地址、端口
	to_address = ('127.0.0.1', 1998)
	# 新建socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# 连接
	sock.connect(address)
	
	```
	对于新建一个socket的时候的`socket.socket(arg1, arg2)`参数选择：
	* `arg1`：代表的是连接地址的参数传入方式，`socket.AF_INET`代表使用`('10.42.0.1', 1998)`这样的元组类型进行传入，还有字符型传入等多种传入方式
	* `arg2`：代表的通讯协议，`socket.SOCK_STREAM`表示使用TCP/IP协议进行通讯。
	**注意：尽量不要使用低于1025的端口。**
* 客户端监听端口，接收请求
	```Python?linenums
	# 建立TCP/IP套接字
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(address)
    # 最大等待连接队列的数量，（连接未接受时候排队的队列）
    sock.listen(5)
	# 接受请求,返回已建立的连接套接字和连接地址详细信息，以后客户端和用户端的通讯就会基于这个conn套接字,这个套接字是一个拥有确定了连接的sock
    conn, addr = sock.accept()
	
	```
  当用户端发送连接请求的时候，服务端便可以接收并进行连接，在连接建立之后，就可以进行信息的交互。
# 数据发送与接收
* 发送数据
  ```
  # 主要数据的长度
  length = encode_byte(len(byte_buf)，32)
  # 发送主要数据的长度数据
  sock.sendall(length)
  # 发送主要数据
  sock.sendall(byte_buf)
  
  ```
  我们发送的数据实际上是可以转换成**比特流**进行发送的，怎么转换自己编写相关程序即可，为了接收不出错，我们先发送主要数据的长度，再发送主要数据，在服务端，也同样先接收被编码为长度为32的主要数据长度数据，再根据这个长度来接收主要数据。
  实际上，发送数据有两种方法
  * `int sock.send(byte_buf)`：不确保数据完全发送，并返回最终发送数据的长度
  * `None sock.sendall(byte_buf)`：确保数据完全发送，无返回值，会发送到数据完全发送或者抛出错误
* 接收数据
  ```
  # 接收主要数据的长度数据
  length = int(sock.recv(32,socket.WAIT_ALL))
  # 基于长度数据接收主要数据
  data = sock.recv(length,socket.WAIT_ALL)
  
  ```
  在进行接收数据的时候，`sock.recv(arg1[,arg2])`可以对数据进行接收。
  * `arg1`：需要接收数据的长度
  * `arg2`：这是个可选参数，如果不进行设置的话那么接收数据的时候就会是最多接收大小为`arg1`的数据，第二个参数设置为`socket.WAIT_ALL`强制接收数据直到数据长度为`arg1`为止。

# 案例部分代码及解析
## github地址
这里是[实例代码的github地址](https://github.com/Reqin/Network-Video-Transmission)

## 服务端
```python?linenums
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

```
## 用户端
```python?linenums
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
    to_address = ('127.0.0.1', 1998)
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


```