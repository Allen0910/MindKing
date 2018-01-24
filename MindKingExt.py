# !/usr/local/bin/python3.6
# -*- coding: utf-8 -*-

import subprocess
import TencentYoutuyun
import requests
import os
import random

from io import BytesIO
from PIL import Image

# 配置坐标信息,根据手机分辨率的不同调整,此坐标可适用于1080 X 1920
config = {
    '头脑王者':{
        'title': (80, 500, 1000, 880),
        'answer': (80, 960, 1000, 1720),
        'point': [
            (316, 993, 723, 1078),
            (316, 1174, 723, 1292),
            (316, 1366, 723, 1469),
            (316, 1570, 723, 1657)
        ]
    }
}

# 1、手机截屏处理
def get_screenshot():
    # 第一个参数为命令行，安卓手机截屏命令；
    # 第二个参数shell=True,在Windows下表示cmd.exe /c即在这里执行的是cmd命令；
    # 第三个参数建立管道,这里通过将stdout重定向到subprocess.PIPE上来取得adb命令的输出
    process = subprocess.Popen('adb shell screencap -p', shell = True, stdout = subprocess.PIPE)
    # 读取二进制数据
    screenshot = process.stdout.read()

    # 可直接保存至文件
    # with open('screenshot.png','wb') as f:
        # f.write(screenshot)

    # 将二进制读进内存中
    imgbyte = BytesIO()
    imgbyte.write(screenshot)
    # 图片处理
    img = Image.open(imgbyte)
    # 切出题目,左上角，右下角的点
    img_Prob = img.crop((config['头脑王者']['title']))
    # 切出答案，左上角，右下角
    img_Ans = img.crop((config['头脑王者']['answer']))
    # 拼接
    new_img = Image.new('RGBA', (920, 1140)) #创建一个新的画布，宽920，高1140
    new_img.paste(img_Prob, (0, 0, 920, 380))
    new_img.paste(img_Ans, (0, 380, 920, 1140))

    # 内存对象
    new_img_byte = BytesIO()
    #保存为png格式至内存中
    new_img.save(new_img_byte, 'png')
    return new_img_byte

# 2、图像OCR识别
def get_content_byimg(img):
    # 这里使用的是腾讯的优图开放平台的图像识别SDK,该appid应该会有上弦，具体不知,如果不能使用了,请自行申请更换
    """ 以下为开放平台返回的识别文本，题目和答案根据此内容解析
    {
        "errorcode":0,
        "errormsg":"OK",
        "items":
                [
                    {
                        "itemstring":"手机",
                        "itemcoord":{"x" : 0, "y" : 1, "width" : 2, "height" : 3},
                        "words": [{"character": "手", "confidence": 98.99}, {"character": "机", "confidence": 87.99}]
                    },
                    {
                        "itemstring":"姓名"，
                        "itemcoord":{"x" : 0, "y" : 1, "width" : 2, "height" : 3},
                        "words": [{"character": "姓", "confidence": 98.99}, {"character": "名", "confidence": 87.99}]
                    }
                ],
        "session_id":"xxxxxx"
    """
    appid = '10115709'
    secret_id = 'AKIDY0HNJ482FJI8mJcqpdIpCPQFwTs6d2kM'
    secret_key = 'fAVfdP1Rlur03vfifR0U5Y1Qwv2yiWHs'
    userid = 'myApp1' # 自行命名,以上三个参数均在开放平台申请

    end_point = TencentYoutuyun.conf.API_YOUTU_END_POINT  # 优图开放平台

    youtu = TencentYoutuyun.YouTu(appid, secret_id, secret_key, userid, end_point)

    with open('screenshot.png', 'wb') as fileReader:
        fileReader.write(img.getvalue())
    # 在执行generalocr()方法时,由于request对象的问题，返回中文时乱码，需要手动再指定返回对象的编码格式：r.encoding='utf-8' 详见youtu,py脚本文件
    ocrinfo = youtu.generalocr('screenshot.png', 0)
    # print(ocrinfo['items'])
    return ocrinfo['items']

# 3、搜索题目答案
def search_ques(question, answers):
    # url = 'https://www.baidu.com/s' # 百度搜索
    url = 'https://www.bing.com/search' # 必应搜索

    # 请求头文件
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7'
    }
    data = {
        # 'wq':question 百度搜索
        'q': question  # 必应搜索
    }
    response = requests.get(url,params=data,headers=headers)
    response.encoding = 'utf-8'
    # 返回请求的文本
    html = response.text
    # print(html)
    # 查找答案并按照答案出现的次数排序
    for i in range(len(answers)):
        answers[i] = (html.count(answers[i]),answers[i],i)
    answers.sort(reverse=True)
    # 打印输出题目和答案
    print(question)
    print(answers)
    # 返回正确答案，即第一个答案
    return answers[0]

# 4、模拟点击手机上答案选项
def click_ans(point):
    cmd = 'adb shell input swipe %s %s %s %s %s' %(
        point[0],
        point[1],
        point[0]+random.randint(0,3), # 右下角的坐标随机点击
        point[1]+random.randint(0,3),
        200
    )
    # 执行cmd命令,根据指定的坐标在手机上模拟点击
    os.system(cmd)

# 主函数
if __name__ == '__main__':

    print('\r\r\n-----------------开始答题-----------------\r\r\n')

    while(True):
        input('输入回车开始答题：')

        # 1、截屏返回图像对象
        img=get_screenshot()

        # 2、图像识别返回识别内容
        infos=get_content_byimg(img)

        # 解析识别的文本内容
        # 一般题目为4个,加上题目至少为5项
        if(len(infos) < 5):
            continue

        # 分割题目和答案
        answers = [x['itemstring'] for x in infos[-4:]] # 后4项为答案
        question = ''.join([x['itemstring'] for x in infos[:-4]]) # 前面为题目

        # 3、百度搜索答案
        res = search_ques(question,answers)

        # 4、点击答案选项
        click_ans(config['头脑王者']['point'][res[2]])