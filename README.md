#### ucas_rushBuy_ticket

为了让大家再也能以"买不到票"为理由不回所，用python实现了购票程序

最好是在连接有线的情况下运行此程序，无线状态下是个玄学问题，老得不到服务器响应，影响买票的速度。

**目前仅支持python2，仅支持微信支付**

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
```

#### 运行

```bash
➜ ucas_rushBuy_ticket git:(master) ✗ python   buyTicket.py
Hi, username: 729173164@qq.com
Password: ******************
Buy bus ticket system
Will use student number 2017E8018661119 to buy a bus ticket.


Login success
[1]:2017-09-28 Thursday
[2]:2017-09-29 Friday
[3]:2017-09-30 Saturday
[4]:2017-10-01 Sunday
hello 王晓满,please choose  the sequence number of the time to take the bus (1-4):
```

选择你要坐车的时间前面的序号，也就是1-4。

```bash
hello 王晓满,please choose  the sequence number of the time to take the bus (1-4):3
[1]:雁栖湖—玉泉路7:20（周末）
[2]:雁栖湖—奥运村7:20（周末）
[3]:雁栖湖—玉泉路13:00（周末）
[4]:雁栖湖—玉泉路15:40（周末）
[5]:玉泉路—雁栖湖6:30（周末）
[6]:玉泉路—雁栖湖10:00（周末）
[7]:玉泉路—雁栖湖15:00（周末）
[8]:奥运村—雁栖湖15:50（周末）
hello 王晓满,please choose  the sequence number of the route to take the bus (1-8):
```

跟上面一样，输入你要乘坐的路线前面的序号。



输入序号后，扫描终端中出现的二维码，进行支付。如果二维码在你的终端里显示的效果不是很好，

可以直接扫描目录下生成的`bug.png`



#### 效果演示

[![asciicast](https://asciinema.org/a/JXPq3VXSuSnbr04DJRM04BNuX.png)](https://asciinema.org/a/JXPq3VXSuSnbr04DJRM04BNuX)












