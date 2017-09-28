#/usr/local/bin/python
#_*_ coding:utf-8 _*_ 


import requests 
from  configparser import RawConfigParser
import re
import time
from collections import OrderedDict  
import json
from urllib import unquote
from qrCodePrinter import QRCodePrinter

debug = False

class BuyTicket():
    def __init__(self):
        cf = RawConfigParser()
        cf.read("config")
        self.username = cf.get("logininfo","username")
        self.password = cf.get("logininfo","password")
        print('Hi, username: ' + self.username)
        print('Password: ' + '*' * len(self.password))
        self.loginPage = 'http://sep.ucas.ac.cn'
        self.loginUrl = self.loginPage + '/slogin'
        self.buyTicketSystem = self.loginPage+"/portal/site/311/1800"
        self.buyTicketHomePage = "http://payment.ucas.ac.cn"
        self.buyTicketIdentity = self.buyTicketHomePage+"/NetWorkUI/sepLogin.htm?Identity="
        self.buyTicketSystemLogin =self.buyTicketHomePage+"/NetWorkUI/sepLoginAction!findbyIdserial.do?idserial="
        self.queryRemainingSeats = self.buyTicketHomePage+"/NetWorkUI/appointmentBus!queryRemainingSeats.action"
        self.queryBusByDate = self.buyTicketHomePage+"/NetWorkUI/appointmentBus!queryBusByDate.action"
        self.getPayProjectId = self.buyTicketHomePage+"/NetWorkUI/reservedBus514R001"
        self.goReserved = self.buyTicketHomePage + "/NetWorkUI/appointmentBus!goReserved.do?"
        self.goPay = self.buyTicketHomePage+"/NetWorkUI/appointmentBus!goPay.action"
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
        self.telNum = ""
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
        loginPage = self.s.get(self.loginPage, headers=self.headers)
        self.cookies = loginPage.cookies

    def __auth(self):
        while True:
            postdata = {
                'userName': self.username,
                'pwd': self.password,
                'sb': 'sb'
            }
            status = self.s.post(self.loginUrl, data=postdata, headers=self.headers)
            if status.status_code != requests.codes.ok:
                continue
            if 'sepuser' in self.s.cookies.get_dict():
                return True
            return False
    def __login(self):
        while True:
            response = self.s.get(self.buyTicketSystem,headers = self.headers)
            print("Buy bus ticket system")
            pattern = re.compile(r"http://payment\.ucas\.ac\.cn/NetWorkUI/sepLogin\.htm\?Identity=([\d\w=&-]*)")
            match = pattern.search(response.text)
            if debug:
                print(match.group(1))
            if not match:
                continue
            buyTicketIdentityReal = self.buyTicketIdentity + match.group(1)
            break
        while True:
            response = self.s.get(buyTicketIdentityReal,headers=self.headers)
            # parttern = re.compile()
            if debug:
                print(response.content)
            pattern = re.compile(r"<option value=\"([\w]*)\">\1</option>")
            match = pattern.search(response.text)
            if not match:
                if "系统正在结账" in response.text.encode("utf8"):
                    print("Sorry,the system is error!")
                    exit()
                continue
            print("Will use student number {} to buy a bus ticket.\n\n".format(match.group(1)))
            buyTicketSystemLoginReal = self.buyTicketSystemLogin+match.group(1)
            break
        while True:

            response = self.s.get(buyTicketSystemLoginReal,headers=self.headers)
            if debug:
                print(response.content)
            pattern = re.compile(r"<a class=\"c4\"  href=\"#\">([\S]*)</a></li>")
            match = pattern.search(response.text)
            if not match:
                continue
            self.studentName = match.group(1).encode("utf8")
            break

    def networkUnstable(self, response):
        if response.status_code != requests.codes.ok:
            if response.status_code == requests.codes.moved_permanently:
                self.__auth()
                self.__login()
                print('Relogin')
            return True
        return False

    def getTicket(self):
        if not  self.__auth():
            print("Login error. Please check your username and password.")
            return 
        else:
            self.__login()
            print("Login success")
        while True:
            response = self.s.get(self.getPayProjectId,headers=self.headers)
            if self.networkUnstable(response):
                continue

            partten = re.compile(r'<input type="hidden" value=\'([\d]*)\' name="payProjectId" id="payProjectId" />')
            match = partten.search(response.text)
            if not match:
                continue
            if  debug:
                print response.text
                print match.group(1)

            self.payProjectId = match.group(1)
            break

        while True:

            while True:
                for i in self.takeBusDay:
                    print("[{i}]:{takeBusDay}".format(i=i,takeBusDay=self.takeBusDay[i]))
                strHint = ("hello {},please choose  the sequence number of the time to take the bus (1-4):".format(self.studentName))
                try:
                    num = int(input(strHint))
                except ValueError as e :
                    continue
                if num > 4 or num < 1:
                    print("The num must between 1-4!")
                    continue
                self.bookingdate = self.takeBusDay[str(num)].split(" ")[0]
                break

            while True:
                postdata = {
                    "bookingdate":self.bookingdate,
                    "factorycode":"R001"
                }

                if debug:
                    print postdata

                response = self.s.post(self.queryBusByDate,headers=self.headers,data=postdata)

                if self.networkUnstable(response):
                    continue
                busRouteData = json.loads(response.text)
                if debug:
                    print(busRouteData["returncode"])

                if busRouteData["returncode"] != "SUCCESS":
                    continue
                i = 1
                for route in busRouteData["routelist"]:
                    self.routeContent[i] = (route["routecode"],route["routename"].encode("utf8"))
                    i = i + 1
                break

            if debug:
                print(self.routeContent)

            for i in self.routeContent:
                print("[{i}]:{routeContent}".format(i=i,routeContent=self.routeContent[i][1]))
            while True:
                strHint = ("hello {},please choose  the sequence number of the route to take the bus (1-{}):".format(self.studentName,i))
                try:
                    num = int(input(strHint))
                except ValueError as e:
                    continue
                if num > i or  num < 1:
                    print("The num must between 1-{i}!".format(i=i))
                    continue
                self.routecode = self.routeContent[num][0]
                break

            while True:
                postdata = {
                    "routecode":self.routecode,
                    "bookingdate":self.bookingdate,
                    "factorycode":"R001"
                }
                if debug:
                    print(postdata)
                response = self.s.post(self.queryRemainingSeats,headers=self.headers,data=postdata)

                if debug:
                    print(response.content)
                if  self.networkUnstable(response):
                    continue

                returnData = json.loads(response.text)
                if debug:
                    print(returnData)
                if not returnData.has_key("returncode")  or returnData["returncode"] != "SUCCESS":
                    print("The webSite doesn't answer to my request. Retrying ...... ")
                    continue
                if int(returnData["returndata"]["freeseat"]) <= 0:  # 神奇的网站，会出现小于零的情况
                    print("Sorry,There are no more tickets left.Please choose other route or time!")
                    break

                self.freeseat = returnData["returndata"]["freeseat"]
                break
            
            print("FreeSeat : "+self.freeseat)
            if debug:
                print "left freeseat:" + self.freeseat

            if (self.freeseat is not "") and (self.freeseat is not "0"):
                break

        while True:
            postdata = {
                "routecode":self.routecode,
                "bookingdate":self.bookingdate,
                "routeName":self.routeContent[num][1],
                "payAmt":"6.00",
                "payProjectId":self.payProjectId,
                "freeseat":self.freeseat
            }
            proxy = {"http":"127.0.0.1:8080"}
            response = self.s.get(self.goReserved,params=postdata,headers=self.headers)
            if self.networkUnstable(response):
                continue
            if debug:
                print response.text

            pattern = re.compile(r"<p >([\d]{11})</p>")
            match = pattern.search(response.text)
            if not match:
                continue
            self.telNum = match.group(1)
            if debug:
                print self.telNum
            break

        while True:
            postdata = {
                "routecode":self.routecode,
                "payAmt":"6.00",
                "bookingdate":self.bookingdate,
                "payProjectId":self.payProjectId,
                "tel":self.telNum,
                "factorycode":"R001"
            }

            response = self.s.post(self.goPay,data=postdata,headers=self.headers)
            if self.networkUnstable(response):
                continue

            returnData = json.loads(response.text)

            if not returnData.has_key("returncode") or returnData["returncode"]!="SUCCESS":
                print(returnData["returnmsg"])
                exit()
            else:
                self.showUserSelectPayType += str(returnData["payOrderTrade"]["id"])
            if debug:
                print self.showUserSelectPayType
            break
        
        while True:
            response = self.s.get(self.showUserSelectPayType,headers=self.headers)
            if self.networkUnstable(response):
                continue
            if debug:
                print response.text

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
            if flag:
                continue
            if debug:
                print postdata
            break
        while True:
            response = self.s.post(self.onlinePay,headers=self.headers,data=postdata,allow_redirects = False)
            if response.status_code != 302:
                print("Sorry,something error!")
                exit()

            redirectUrl = response.headers["Location"]
            if debug:
                print(redirectUrl)

            self.payStr =  unquote(redirectUrl.split("&")[2].split("=")[1])
            if debug:
                print self.payStr
            break

        qr = QRCodePrinter(self.payStr)
        qr.printQR()
        print("\n\nPlease use Wechat  scan this QR  or buy.png to pay for your ticket!")

if __name__ == '__main__':
    buyTicket = BuyTicket()
    buyTicket.getTicket()






