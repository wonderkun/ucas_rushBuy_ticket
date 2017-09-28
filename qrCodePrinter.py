#/usr/bin/local/python
#_*_ coding:utf-8 _*_


import platform 
import qrcode 


class QRCodePrinter():
    def __init__(self,codeStr):
        self.codeStr = codeStr
        self.codeArray = [] 
        # 保存生成二维码的字符串  
        self.platform = self.__getSystemType()
        if "Windows" in self.platform:
            self.black = "▇"
            self.white = " "
        elif "Linux" in self.platform:
            self.black = "\033[40m  \033[0m"
            self.white = "\033[47m  \033[0m"
        else:
            self.black = "\033[40m  \033[0m"
            self.white = "\033[47m  \033[0m"
        
        self.createQR()

    def __getSystemType(self):
        return platform.platform()+":"+platform.architecture()[0]

    def createQR(self):
        # save QR code 
        qrSave =qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
        )
        qrSave.add_data(self.codeStr)
        qrSave.make(fit=True)
        imgSave = qrSave.make_image()
        imgSave.save("buy.png")

        ## print QR code 
        qrPrite = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
        )
        qrPrite.add_data(self.codeStr)
        qrPrite.make(fit=True)
        img = qrPrite.make_image()
        # img.save('buy.png')
        imgL = img.convert("L")
        width = imgL.size[0]  
        height = imgL.size[1] 
        codeArray = []

        for h in range(0, height):
            row = []  
            for w in range(0, width):  
                pixel = imgL.getpixel((w, h)) 
                row.append(pixel)
            codeArray.append(row)
        self.codeArray = codeArray

    def printQR(self):
        for i in self.codeArray:
            str = ""
            for j in i:
                if j == 255:
                    str+=self.white # 是1表示白色，0表示黑色
                else:
                    str+=self.black
            # str += "\n"
            print(str)

if __name__=="__main__":
    pr = QRCodePrinter("testtesttesttesttesttesttesttesttesttest")
    pr.printQR()
