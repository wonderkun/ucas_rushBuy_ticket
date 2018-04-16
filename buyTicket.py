#/usr/local/bin/python
#_*_coding:utf-8_*_ 
 
import requests 
import sys
from  configparser import RawConfigParser
import re
import time
from collections import OrderedDict  
import json
from qrCodePrinter import QRCodePrinter
import platform
import datetime
import threading
if platform.python_version()[0] == "2" :
    print("[*] Please use python3!")
    sys.exit(0)
elif  platform.python_version()[0] == "3" :
    from urllib.parse import unquote

debug = False

class BuyTicket(threading.Thread):
    
    def requestRetry(retryTime = 5,condition=None):
        '''
           retryTime 是重试次数
           condition 是退出条件
        '''
        def _retry(function):
            def __retry(*args,**kwargs):
                count = 0
                result = None
                while count < retryTime:
                    try:
                        result = function(*args,**kwargs)
                    except Exception as e:
                        print(e)
                        pass
                    if result == condition:
                        return result
                    else :
                        count += 1
                        print("Retry run function %s  %s times" %(function.__name__,count))
                        time.sleep(2)
                print("Run function %s error "%(function.__name__))
                return result
            return __retry
        return _retry               

    def __init__(self,username,password,telNum,autoRecognize=False):
        threading.Thread.__init__(self)
        self.username = username
        self.password = password
        self.routeName = None
        self.telNum = telNum
        self.captchaFile = "captcha.png"
        self.payFile = "buy.png"
        self.code = None
        self.studentNum = ""
        self.studentName = ""
        self.timeout = 8
        self.autoRecognize = int(autoRecognize)
        if self.autoRecognize:
            from autoCaptcha import recognize
            self.recognize = recognize.Recognize(self.captchaFile)


        print('Hi, username: ' + self.username)
        print('Password: ' + '*' * len(self.password))
        
        self.platform = platform.platform()
        self.loginPage = 'http://sep.ucas.ac.cn'
        self.loginUrl = self.loginPage + '/slogin'
        self.buyTicketSystem = self.loginPage+"/portal/site/311/1800"
        self.buyTicketHomePage = "http://payment.ucas.ac.cn"
        self.buyTicketIdentity = self.buyTicketHomePage+"/NetWorkUI/sepLogin.htm?Identity="
        self.buyTicketSystemLogin =self.buyTicketHomePage+"/NetWorkUI/sepLoginAction!findbyIdserial.do?idserial="
        self.queryRemainingSeats = self.buyTicketHomePage+"/NetWorkUI/queryRemainingSeats"
        self.queryBusByDate = self.buyTicketHomePage+"/NetWorkUI/queryBusByDate"
        self.getPayProjectId = self.buyTicketHomePage+"/NetWorkUI/reservedBus514R001"
        self.goReserved = self.buyTicketHomePage + "/NetWorkUI/openReservedBusInfoConfirm"
        self.goPay = self.buyTicketHomePage+"/NetWorkUI/reservedBusCreateOrder"
        self.showUserSelectPayType = self.buyTicketHomePage+"/NetWorkUI/showUserSelectPayType25"
        self.onlinePay = self.buyTicketHomePage+"/NetWorkUI/onlinePay"

        self.time = time.time()
        self.strTime = lambda x:time.strftime("%Y-%m-%d %A",time.localtime(x))
        self.takeBusDay = OrderedDict(
            [("1",self.strTime(self.time)),
            ("2",self.strTime(self.time+24*60*60)),
            ("3",self.strTime(self.time+24*60*60*2)),
            ("4",self.strTime(self.time+24*60*60*3))]
        )

        self.routeContent = OrderedDict()
        self.bookingdate = ""
        self.routecode = ""
        self.freeseat = ""
        self.payProjectId = ""
        self.payStr = ""

        self.headers = {
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        }
        
        self.s = requests.Session()
        
    def __systemExit(self,message):
        print(message)
        sys.exit(0)

    @requestRetry(3,True)
    def __getCaptcha(self):
        loginPage = self.s.get(self.loginPage, headers=self.headers,timeout=self.timeout)
        flag = '<img id="code" src="/changePic"><a href="javascript:changeimg()">看不清，换一张 </a>'in loginPage.text
        
        if flag:
            self.captcha = self.loginPage+"/changePic"
            print("I find the captcha:%s"%(self.captcha))
            with open(self.captchaFile,'wb') as file: 
                file.write(self.s.get(self.captcha).content)
                file.close()
        else:
            self.captcha = None
        return True
   
    def __waitForCap(self):
        if getattr(self,"captcha",None) is not None:
            if not self.autoRecognize:
                self.code = str(input("[*] Please input the captcha. The captcha picture is in ./%s:"%(self.captchaFile)))
                if len(self.code)!=4:
                    self.__systemExit("[*] The captcha is error!")
            else:
                self.code = self.recognize.crack_captcha()
        return True
        
    @requestRetry(10,True)
    def __auth(self):
        if not self.__getCaptcha():
            self.__systemExit("[*] Get captcha error!")
        self.__waitForCap()
        postdata = {
            'userName': self.username,
            'pwd': self.password,
            'sb': 'sb',
            'certCode':self.code
        }
        status = self.s.post(self.loginUrl, data=postdata, headers=self.headers,timeout=self.timeout)
        if status.status_code != requests.codes.ok:
            return False
        if 'sepuser' in self.s.cookies.get_dict():
            return True

        self.code = None
        # print("[*] 对不起，可能是验证码或者用户名密码错误，咱们再来一次!")
        print("[*] Sorry,captcha , username or password error. Let's try again!")
        return False
        
    @requestRetry(10,True)
    def __getBuyTicketIdentityReal(self):
        response = self.s.get(self.buyTicketSystem,headers = self.headers,timeout=self.timeout)
        print("Buy bus ticket system")
        pattern = re.compile(r"http://payment\.ucas\.ac\.cn/NetWorkUI/sepLogin\.htm\?Identity=([\d\w=&-]*)")
        match = pattern.search(response.text)
        if debug:
            print(match.group(1))
        if not match:
            return False
        self.buyTicketIdentityReal = self.buyTicketIdentity + match.group(1)
        return True
    
    @requestRetry(10,True)
    def __getBuyTicketSystemLoginReal(self):
        response = self.s.get(self.buyTicketIdentityReal,headers=self.headers,timeout=self.timeout)
            # parttern = re.compile()
        if debug:
            print(response.content)
        pattern = re.compile(r"<option value=\"([\w]*)\">\1</option>")
        match = pattern.search(response.text)
        if not match:
            if "系统正在结账" in response.text:
                print("Sorry,the system is checking out!")
                sys.exit(0)
            return False
        print("[*] Will use student number {} to buy a bus ticket.\n".format(match.group(1)))
        self.studentNum = match.group(1)
        # self.friend.send("Will use student number {} to buy a bus ticket.\n".format(match.group(1)))
        self.buyTicketSystemLoginReal = self.buyTicketSystemLogin+match.group(1)
        return True

    @requestRetry(3,True)
    def __getStudentName(self):
        response = self.s.get(self.buyTicketSystemLoginReal,headers=self.headers,timeout=self.timeout)
        if debug:
            print(response.content)
        pattern = re.compile(r"<a class=\"c4\"  href=\"#\">([\S]*)</a></li>")
        match = pattern.search(response.text)
        if not match:
            return False
        self.studentName = match.group(1)
        return True
    def __login(self):            
        if   self.__getBuyTicketIdentityReal() and self.__getBuyTicketSystemLoginReal() and self.__getStudentName():
            return True
        return False

    @requestRetry(4,True)
    def __getPayProjectId(self):
        response = self.s.get(self.getPayProjectId,headers=self.headers,timeout=self.timeout)
        if self.networkUnstable(response):
            return False
        partten = re.compile(r'<input type="hidden" value=\'([\d]*)\' name="payProjectId" id="payProjectId" />')
        match = partten.search(response.text)
        if not match:
            if "系统正在结账" in response.text:
                # print("[*] 系统正在结账!")
                self.__systemExit("[*] The system is checking out. We cann't by ticket now!")
            return False
        if  debug:
            print(response.text)
            print(match.group(1))
        self.payProjectId = match.group(1)
        print("[*] %s run Success."%(sys._getframe().f_code.co_name))
        return True

    @requestRetry(5,True)
    def __getBusRouteData(self):
        for i in self.takeBusDay:
            print("[{i}]:{takeBusDay}".format(i=i,takeBusDay=self.takeBusDay[i]))
        if "Windows" in self.platform:
            strHint = ("hello {},please choose  the sequence number of the time to take the bus (1-4):".format(self.studentName))
        else:  
            strHint = ("hello {},please choose  the sequence number of the time to take the bus (1-4):".format(self.studentName))
        try:
            num = int(input(strHint))
        except  ValueError as e:
            return False
        if num > 4 or num < 1:
            print("[*] The num must between 1-4!")
            return False

        print("[*] %s run Success."%(sys._getframe().f_code.co_name))
        self.bookingdate = self.takeBusDay[str(num)].split(" ")[0]
        if not self.bookingdate:
            return False
        return True

    @requestRetry(50,True)
    def __getBusRouteContent(self):
        postdata = {
            "bookingdate":self.bookingdate,
            "factorycode":"R001"
        }
        response = self.s.post(self.queryBusByDate,headers=self.headers,data=postdata,timeout=self.timeout)
        if self.networkUnstable(response):
            return False
        busRouteData = json.loads(response.text)           
        if  "returncode" not in busRouteData or busRouteData["returncode"] != "SUCCESS":
            return False
        i = 1
        for route in busRouteData["routelist"]:
            self.routeContent[i] = (route["routecode"],route["routename"])
            i = i + 1
        print("[*] %s run Success."%(sys._getframe().f_code.co_name))
        return True
        
    @requestRetry(5,True)
    def __getRouteCode(self):
        self.routeCode = None        
        for i in self.routeContent:
            if "Windows" in self.platform:
                print("[{i}]:{routeContent}".format(i=i,routeContent=self.routeContent[i][1]))
            else:
                print("[{i}]:{routeContent}".format(i=i,routeContent=self.routeContent[i][1]))

        if "Windows" in self.platform:
            strHint = ("hello {},please choose  the sequence number of the route to take the bus (1-{}):".format(self.studentName,i))
        else:
            strHint = ("hello {},please choose  the sequence number of the route to take the bus (1-{}):".format(self.studentName,i))
        try:
            num = int(input(strHint))
        except ValueError as e :
            return False
        if num > i or  num < 1:
            print("[*] The num must between 1-{i}!".format(i=i))
            return False
        
        self.routecode = self.routeContent[num][0]
        self.routeName = self.routeContent[num][1]
        if self.routecode == None:
            print("[*] Sorry,the route your ordered is not exists!")
            # self.friend.send("sorry,妳预定的路线不存在!")
            return False
        print("[*] %s run Success."%(sys._getframe().f_code.co_name))
        return True

    @requestRetry(50,True)
    def __getRemainingSeats(self):
        postdata = {
                    "routecode":self.routecode,
                    "bookingdate":self.bookingdate,
                    "factorycode":"R001"
                }
        # print(postdata)
        response = self.s.post(self.queryRemainingSeats,headers=self.headers,data=postdata,timeout=self.timeout)
        if  self.networkUnstable(response):
            return False
        returnData = json.loads(response.text)
        # print(returnData)
        if "returncode" not in returnData  or returnData["returncode"] != "SUCCESS":
            print("[*] The webSite doesn't answer to my request. Retrying ...... ")
            return False    
        if int(returnData["returndata"]["freeseat"]) <= 0:  # 神奇的网站，会出现小于零的情况
            # self.friend.send("这辆车没有余票了，好伤心啊！555555 ~")
            print("[*] Sorry,There are no more tickets left.Please choose other route or time!")
            sys.exit(0)
        self.freeseat = returnData["returndata"]["freeseat"]
        if (self.freeseat is  "") or (self.freeseat is  "0"):
            return False
        print("[*] %s %s has freeSeat : %s" %(self.bookingdate,self.routeName,self.freeseat))
        print("[*] %s run Success."%(sys._getframe().f_code.co_name))
        return True

    @requestRetry(50,True)
    def __getReservedBusInfo(self):
        postdata = {
                "carno":"00013",
                "routecode":self.routeCode,
                "bookingdate":self.bookingdate,
                "routeName":self.routeName,
                "payamtstr":"6.00",
                "payAmt":"6.00",
                "payProjectId":self.payProjectId,
                "freeseat":self.freeseat,
                "factorycode":"R001"
            }

        response = self.s.post(self.goReserved,data=postdata,headers=self.headers,timeout=self.timeout)
        if self.networkUnstable(response):
            return False
        print("[*] %s run Success."%(sys._getframe().f_code.co_name))
        return True
        
    @requestRetry(10,True)
    def __seletePayType(self):
        print("Your telephone number is: %s"%(self.telNum))
        postdata = {
                "routecode":self.routecode,
                "payAmt":"6.00",
                "bookingdate":self.bookingdate,
                "payProjectId":self.payProjectId,
                "tel":self.telNum,
                "factorycode":"R001"
        }
        response = self.s.post(self.goPay,data=postdata,headers=self.headers,timeout=self.timeout)
        if self.networkUnstable(response):
            return False
        returnData = json.loads(response.text)
        if  "returncode" not in returnData or returnData["returncode"]!="SUCCESS":
            
            print(returnData["returnmsg"])
            sys.exit(0)
        else:
            if  "payOrderTrade" in returnData and  "id" in returnData["payOrderTrade"]:
                self.showUserSelectPayType += str(returnData["payOrderTrade"]["id"])
                print("[*] %s run Success."%(sys._getframe().f_code.co_name))
                return True
            return False  

    @requestRetry(10,True)
    def __goPay(self):
        response = self.s.get(self.showUserSelectPayType,headers=self.headers,timeout=self.timeout)
        if self.networkUnstable(response):
            return False
        postdata={
            "start_limittxtime":"",
            "end_limittxtime":"",
            "payType":"03",
        }
        reList = [
                r"<input type=\"hidden\" value=\'(?P<value>[\w]*)\'   name=\"(?P<name>[\w]*)\" id=\"orderno\" />",
                r"<input type=\"hidden\" value='(?P<value>[\S]*)' name=\"(?P<name>[\w]*)\" id=\"orderamt\" />",
                r"<input type=\"hidden\" id=\"mess\" value=\"(?P<value>[\S]*)\" name=\"(?P<name>[\w]*)\"/>",
                r"<input type=\"hidden\" name=\"(?P<name>[\S]*)\" value=\"(?P<value>[\w]*)\" />",
                r"<input type=\"hidden\" name=\"(?P<name>[\w]*)\" value=\"(?P<value>[\S]*)\" />"
        ]
        flag = False
        for c in reList:
            partten = re.compile(c)
            match = partten.search(response.text)
            if not match:
                flag = True
                break
            else:
                postdata[match.group("name")] = match.group("value")
        
        print("[*] %s run Success."%(sys._getframe().f_code.co_name))
        # print postdata
        self.__onlinePay(postdata)
        return True

    @requestRetry(10,True)
    def __onlinePay(self,postdata):
        response = self.s.post(self.onlinePay,headers=self.headers,data=postdata,allow_redirects = False,timeout=self.timeout)
        if response.status_code != 302:
            print("[*] Sorry,something error!")
            sys.exit(0)
        redirectUrl = response.headers["Location"]    
        # print(redirectUrl)
        response = self.s.get(self.buyTicketHomePage+redirectUrl,headers=self.headers,allow_redirects = False,timeout=self.timeout)
        if response.status_code != 302:
            print("[*] Sorry,something error!")
            sys.exit(0)
        redirectUrl = response.headers["Location"]
        # print redirectUrl
        self.payStr =  unquote(redirectUrl.split("&")[2].split("=")[1])
        # print self.payStr
        if "Windows" in self.platform:
            print("\n\n购票信息:\n用户名:{}\n学号:{}\n乘车日期:{}\n乘车路线:{}\n电话号码:{}\n如果以上信息无误,请扫下面的二维码进行支付，支付前务必核对购票信息".format(self.username,self.studentNum,self.bookingdate,self.routeName,self.telNum))
        else:
            print("\n\n购票信息:\n用户名:{}\n学号:{}\n乘车日期:{}\n乘车路线:{}\n电话号码:{}\n如果以上信息无误,请扫下面的二维码进行支付，支付前务必核对购票信息。".format(self.username,self.studentNum,self.bookingdate,self.routeName,self.telNum))
        print("[*] %s run Success."%(sys._getframe().f_code.co_name))
        return True
    def networkUnstable(self, response):
        if response.status_code != requests.codes.ok:
            if response.status_code == requests.codes.moved_permanently:
                self.__auth()
                self.__login()
                print('Relogin!')
            return True
        return False

    def run(self):
        if not  self.__auth():
            print("[*] Login error,please check your username and password.")
            return
        if not self.__login():
            print("[*] Login into buy ticket system error!")
            return
        print("[*] Login into system success!")
        
        if not self.__getPayProjectId():
            return
        if not self.__getBusRouteData():
            return 
        if not self.__getBusRouteContent():
            return
        if not self.__getRouteCode():
            return
        if not self.__getRemainingSeats():
            return
        if not self.__getReservedBusInfo():
            return 
        if not self.__seletePayType():
            return 
        if not self.__goPay():
            return
        qr = QRCodePrinter(self.payStr,fileName=self.payFile)
        qr.printQR()
        # print("\nBuy ticket success!")
        print("\n\n[*] Please use Wechat  scan this QR  or buy.png to pay for your ticket!")
        
if __name__ == '__main__':
    cf = RawConfigParser()
    cf.read("config")
    username = cf.get("logininfo","username")
    password = cf.get("logininfo","password")
    phonenum = cf.get("logininfo","phoneNum")
    autoRecognize = cf.get("logininfo","autoRecognize")
    buyTicket = BuyTicket(username=username,password=password,telNum=phonenum,autoRecognize=autoRecognize)
    buyTicket.setDaemon(True)
    buyTicket.start()
    while buyTicket.is_alive():
        time.sleep(1)
        






