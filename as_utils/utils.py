# --*-- coding:utf8 --*--
import time
import socket
import cv2
import numpy as np


def buf_encode(data, length):
    return str.encode(str(data).ljust(length))


def collect_buf(sock, length):
    buf = b''  # buf是一个byte类型
    while length:
        try:
            # 接受TCP套接字的数据。数据以字符串形式返回，count指定要接收的最大数据量.
            new_buf = sock.recv(length, socket.MSG_WAITALL)
            if not new_buf:
                return None
            buf += new_buf
            length -= len(new_buf)
        except socket.error as e:
            print(e)
            time.sleep(1)
            continue
    return buf


def next_frame(file):
    try:
        _, frame_next = file.read()
        return frame_next
    except cv2.error as error:
        print('io11', error)
        # return None


def encode(image, q=100):
    try:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), q]
        result, encoded = cv2.imencode('.jpg', image, encode_param)
        return np.array(encoded)
    except cv2.error as e:
        print(e)
        return None
