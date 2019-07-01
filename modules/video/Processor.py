# coding:utf8

import cv2
import numpy as np


class Processor:

    def __init__(self, source):
        self.source = None
        self.frame = None
        self.frame_encoded = None
        self.__set_source(source)

    def __set_source(self, source):
        try:
            source = int(source)
            self.source = cv2.VideoCapture(source)
        except Exception:
            print(Exception)
            self.source = cv2.VideoCapture(source)

    def next_frame(self):
        _, frame = self.source.read()
        self.frame = frame
        return self

    def encode(self, q=100):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), q]
        result, encoded = cv2.imencode('.jpg', self.frame, encode_param)
        self.frame = encoded
        self.frame_encoded = encoded
        return self

    @staticmethod
    def decode(frame):
        data_decoded = np.frombuffer(frame, np.uint8)
        return cv2.imdecode(data_decoded, cv2.IMREAD_COLOR)
