#coding=utf-8
from PIL import Image,ImageEnhance,ImageFilter
import numpy as np
import tensorflow as tf
import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
import random

class  Recognize:
    IMAGE_HEIGHT = 30
    IMAGE_WIDTH = 30
    MAX_CAPTCHA = 1
    CHAR_SET_LEN = 10
    handle_loc = './tmp/'
    X = tf.placeholder(tf.float32, [None, IMAGE_HEIGHT*IMAGE_WIDTH])
    Y = tf.placeholder(tf.float32, [None, MAX_CAPTCHA*CHAR_SET_LEN])
    keep_prob = tf.placeholder(tf.float32)
    
    def crack_captcha(self):
        pic_addr = self.pic_addr
        self.handle_image(pic_addr)
        n = 1
        result = ''
        while n <= 4:
            text, image = self.get_name_and_image(n)
            image = 1 * (image.flatten())
            predict = tf.argmax(tf.reshape(self.output, [-1, self.MAX_CAPTCHA, self.CHAR_SET_LEN]), 2)
            text_list = self.sess.run(predict, feed_dict={self.X: [image], self.keep_prob: 1})
            vec = text_list[0].tolist()
            #print(vec)
            predict_text = self.vec2name(vec)
            #print(predict_text)
            result = result + predict_text
            n += 1
        return result
    def crack_captcha_cnn(self,w_alpha=0.01, b_alpha=0.1):
        x = tf.reshape(self.X, shape=[-1, self.IMAGE_HEIGHT, self.IMAGE_WIDTH, 1])
        # 3 conv layer
        w_c1 = tf.Variable(w_alpha * tf.random_normal([2, 2, 1, 32]))
        b_c1 = tf.Variable(b_alpha * tf.random_normal([32]))
        conv1 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(x, w_c1, strides=[1, 1, 1, 1], padding='SAME'), b_c1))
        conv1 = tf.nn.max_pool(conv1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        conv1 = tf.nn.dropout(conv1, self.keep_prob)

        w_c2 = tf.Variable(w_alpha * tf.random_normal([2, 2, 32, 64]))
        b_c2 = tf.Variable(b_alpha * tf.random_normal([64]))
        conv2 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv1, w_c2, strides=[1, 1, 1, 1], padding='SAME'), b_c2))
        conv2 = tf.nn.max_pool(conv2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        conv2 = tf.nn.dropout(conv2, self.keep_prob)

        w_c3 = tf.Variable(w_alpha * tf.random_normal([2, 2, 64, 64]))
        b_c3 = tf.Variable(b_alpha * tf.random_normal([64]))
        conv3 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv2, w_c3, strides=[1, 1, 1, 1], padding='SAME'), b_c3))
        conv3 = tf.nn.max_pool(conv3, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        conv3 = tf.nn.dropout(conv3, self.keep_prob)

        # Fully connected layer
        w_d = tf.Variable(w_alpha * tf.random_normal([4 * 4 * 64, 1024]))
        b_d = tf.Variable(b_alpha * tf.random_normal([1024]))
        dense = tf.reshape(conv3, [-1, w_d.get_shape().as_list()[0]])
        dense = tf.nn.relu(tf.add(tf.matmul(dense, w_d), b_d))
        dense = tf.nn.dropout(dense, self.keep_prob)

        w_out = tf.Variable(w_alpha * tf.random_normal([1024, self.MAX_CAPTCHA * self.CHAR_SET_LEN]))
        b_out = tf.Variable(b_alpha * tf.random_normal([self.MAX_CAPTCHA * self.CHAR_SET_LEN]))
        out = tf.add(tf.matmul(dense, w_out), b_out)
        return out

    def get_name_and_image(self,i):
        #all_image = os.listdir(handle_loc)
        #print(all_image)
        base = os.path.basename(self.handle_loc + str(i) + '.jpg')
        name = os.path.splitext(base)[0]
        image = Image.open(self.handle_loc + str(i) + '.jpg')
        image = np.array(image)
        return name, image

    def handle_image(self,pic_addr):
        #对原始图片进行处理，包括切割和灰度化两个部分
        base = os.path.basename(pic_addr)
        name = os.path.splitext(base)[0]
        #将图片转为灰度图片，单通道图片
        im = Image.open(pic_addr)
        im = im.convert('L')
        #对图片进行切割处理，处理结果存到特定位置，分别名命为1234
        box1 = (0, 0, 30, 30)
        im1 = im.crop(box1)
        name1 = self.handle_loc + '1.jpg'    
        im1.save(name1)
        box2 = (25, 0, 55, 30)
        im2 = im.crop(box2)
        name2 = self.handle_loc + '2.jpg' 
        im2.save(name2)
        box3 = (45, 0, 75, 30)
        im3 = im.crop(box3)
        name3 = self.handle_loc + '3.jpg'
        im3.save(name3)
        box4 = (70, 0, 100, 30)
        im4 = im.crop(box4)
        name4 = self.handle_loc + '4.jpg'
        im4.save(name4)

    def __init__(self,pic_addr):
        self.pic_addr = pic_addr
        self.output = self.crack_captcha_cnn()
        self.saver = tf.train.Saver()
        # with tf.Session() as sess:
        self.sess = tf.Session()
        self.saver.restore(self.sess,tf.train.latest_checkpoint('./autoCaptcha/'))
                                
    def vec2name(self,vec):
        name = []
        for i in vec:
            a = chr(i + 48)
            name.append(a)
        return "".join(name)
    

if __name__ == '__main__':
    import requests
    for i in range(1):
        url  = 'http://sep.ucas.ac.cn/changePic'
        with open(str(i) + 'pic.jpg','wb')  as fileH:
            fileH.write(requests.get(url).content)
            fileH.close()
            # num = crack_captcha(str(i) + "pic.jpg")
            # print(num)
            cracker = Recognize(str(i) + 'pic.jpg')
            print(cracker.crack_captcha())
