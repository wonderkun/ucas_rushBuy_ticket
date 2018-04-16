# ucas_rushBuy_ticket

快速qiangpiao程序



## 修改 

1. 配置文件做了修改，需要输入手机号码
2. 添加了验证码部分，在学校外网的时候，也可以通过手工输入验证码或者自动识别验证码（感谢教授同学用高端的机器学习开发的验证码自动识别部分，可以在配置文件中开启是否启用自动识别功能）
3. 修改了代码的结构，在网络比较差的时候，也可以运行
4. 目前仅支持python3
5. 配置文件中 autoRecognize为1，代表开启自动验证码识别，为0是关闭自动识别

**用自动识别功能需要安装tensorflow，但是windows用户需要安装python3.5，因为tensorflow在windows上仅支持python3.5版本**
**目前仅支持python3，仅支持微信支付，使用之前请详细阅读README.md**

## 使用步骤

#### 依赖库 requests,pillow,qrcode

```bash
# 安装库依赖
pip install requests 
pip install pillow 
pip install qrcode 

# 请确保你的requests是最新版的(老版本存在一些bug),如果不是最新版，用如下命令升级
pip install --upgrade requests 
```

#### 修改配置文件config

```bash
[logininfo]
username = 学校统一验证平台的邮箱
password = 你的密码
phonenum = 你的电话号码
```

#### 运行

```bash
➜ ucas_rushBuy_ticket git:(master) ✗ python   buyTicket.py
Hi, username: ***********
Password: ******************
Buy bus ticket system
Will use student number 2017E8018661119 to buy a bus ticket.


Login success
[1]:2017-09-28 Thursday
[2]:2017-09-29 Friday
[3]:2017-09-30 Saturday
[4]:2017-10-01 Sunday
hello **********,please choose  the sequence number of the time to take the bus (1-4):
```

选择你要坐车的时间前面的序号，也就是1-4。

```bash
hello ******,please choose  the sequence number of the time to take the bus (1-4):3
[1]:雁栖湖—玉泉路7:20（周末）
[2]:雁栖湖—奥运村7:20（周末）
[3]:雁栖湖—玉泉路13:00（周末）
[4]:雁栖湖—玉泉路15:40（周末）
[5]:玉泉路—雁栖湖6:30（周末）
[6]:玉泉路—雁栖湖10:00（周末）
[7]:玉泉路—雁栖湖15:00（周末）
[8]:奥运村—雁栖湖15:50（周末）
hello ************,please choose  the sequence number of the route to take the bus (1-8):
```

跟上面一样，输入你要乘坐的路线前面的序号。



输入序号后，扫描终端中出现的二维码，进行支付。如果二维码在你的终端里显示的效果不是很好，

可以直接扫描目录下生成的`bug.png`



#### 效果演示

[![asciicast](https://asciinema.org/a/JXPq3VXSuSnbr04DJRM04BNuX.png)](https://asciinema.org/a/JXPq3VXSuSnbr04DJRM04BNuX)













