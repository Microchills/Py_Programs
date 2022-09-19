import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import requests
from lxml import etree

class Page(object):
    def __init__(self,url,params):
        self.url = url
        self.params = params
    
    # def setParams(self,params):
    #     self.params = params

    def getPage(self):
        headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.27'
        }
        try:
            response = requests.get(self.url,params=self.params,headers=headers)
            if response.status_code == 200:
                html = etree.HTML(response.text)
                return html
            print('Error:get invalid respone %s' %(response.status_code))
        except requests.RequestException:
            print('Error occurred while scraping %s' %(self.url))

    def showInfo(self):
        key = self.params['keyword'] 
        page = self.params['page']
        print('Scraping %s... %sPage%s' %(self.url,key,page))

class KeyPage(Page):
    def __init__(self,url,params):
        super().__init__(url,params)
    
    def getKey(self):
        html = self.getPage()
        path = '//div[@class="catergories"]//div[5]//div//div'
        keyDiv = html.xpath(path)
        keyDict = {}
        for div in keyDiv:
            keyText = div.xpath('.//a/text()')
            keyDict[keyText[0]] = keyText[1:]
        return keyDict

class ListPage(Page):
    def __init__(self,url,params):
        super().__init__(url,params)
    
    def getMaxPage(self):
        html = self.getPage()
        path = '//ul[@class="el-pager"]//li[last()]/text()'
        MaxPage = html.xpath(path)[0]
        return int(MaxPage)
        
    def getUrl(self):
        html = self.getPage()
        path = '//div[@class="f-l intern-detail__job"]//a/@href'
        urlList = html.xpath(path)
        return urlList
 
class Frame(object):
    def __init__(self,root,row,name,keyList):
        frame = ttk.Labelframe(root,text=name,labelanchor="nw",bootstyle='primary')
        frame.grid(row=row,columnspan=10,padx=10,pady=10,sticky='w')
        self.frame = frame
        self.keyList = keyList
        self.btnList = []
        self.btnVarList = []
        
    def packKeys(self):
        for key in self.keyList:
            v = ttk.IntVar()
            b = ttk.Checkbutton(self.frame,text=key,variable=v,
                                bootstyle='success-outline-toolbutton')
            b.grid(row=1,column=self.keyList.index(key),padx=5,pady=5)
            self.btnVarList.append(v)
            self.btnList.append(b)
    def ChoosenKeys(self):
        choosenKeys =[]
        for i in range(len(self.keyList)):
            if self.btnVarList[i].get():
                choosenKeys.append(self.keyList[i])
        return choosenKeys

