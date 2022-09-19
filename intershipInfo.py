from lxml import etree
import asyncio
import aiohttp
import time
import re
import pandas as pd
import multiprocessing
from multiprocessing import Lock,Manager
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import myClasses as myCls

# defined as coroutine object to improve efficiency
async def detailPage(url,dataList):
    async with aiohttp.ClientSession() as session:
        async with await session.get(url) as response:
            html = etree.HTML(await response.text())
            job_name = html.xpath('//div[@class="new_job_name"]/span/text()')
            job_salary = html.xpath('//span[@class="job_money cutom_font"]/text()')
            job_week = html.xpath('//span[@class="job_week cutom_font"]/text()')
            job_time = html.xpath('//span[@class="job_time cutom_font"]/text()')
            job_details = html.xpath('//div[@class="job_detail"]/*/text()')
            job_location = html.xpath('//span[@class="com_position"]/text()')
            # job_location = html.xpath('//div[@class="con-job job_city"]/span[1]/text()')
            com_name = html.xpath('//a[@class="com-name"]/text()')
            com_desc = html.xpath('string(//a[@class="com-name"]/following-sibling::div)')
            saveData(job_name,job_salary,job_week,job_time,job_details,
                        job_location,com_name,com_desc,dataList)

# save the job information scraped to a List
def saveData(job_name,job_salary,job_week,job_time,job_details,
                job_location,com_name,com_desc,dataList):
    jobData = {
        'job_name': ''.join(job_name),
        'job_salary': ''.join(job_salary),
        'job_week': ''.join(job_week),
        'job_time': ''.join(job_time),
        # eliminating the '\n''\t' among the information and removing blank
        'job_details': ''.join([deta for deta in [re.sub('\\s', '',detail) 
                       for detail in job_details] if deta != '']),
        'job_location': job_location,
        'com_name': re.sub('\\s','',''.join(com_name)),
        'com_desc': com_desc,
    }
    dataList.append(jobData)
    
def getUrlList(key):
    url = 'https://www.shixiseng.com/interns'
    params = {'page':1,'keyword':key,'city':"上海"}
    maxPage = myCls.ListPage(url,params).getMaxPage()
    page = 1
    urlList = []
    while (True):
        params = {'keyword':key,'page':page,'city':"上海"}
        listpage = myCls.ListPage(url,params)
        listpage.showInfo()
        urlList += listpage.getUrl()
        if (page < maxPage):
            page += 1
        else:
            break
    print("Scraping details and Saving...%s" %key)
    return urlList

def getAndSave(key,keyDict,lock):
    urlList = getUrlList(key)
    #save number of data scraped for each key
    with lock:
        keyDict[key] = len(urlList)
    #save .json data with a list
    dataList = []
    loop = asyncio.get_event_loop()
    tasks = [asyncio.ensure_future(detailPage(url,dataList))
             for url in urlList]
    loop.run_until_complete(asyncio.wait(tasks))
    #save data to jobData.csv
    df = pd.DataFrame(dataList)
    df.index += 1
    df.to_csv("{0}_{1}.csv".format(key,"实习数据"),
              encoding="utf-8-sig")

def startScraping(keyDict):
    start = time.time()
    #using manager to save number of data scraped in multiprocessing
    process_list = []
    lock = Lock()
    with Manager() as m:
        keyDict = m.dict(keyDict)
        for key in keyDict.keys():
            p = (multiprocessing.Process
                (target=getAndSave,args=(key,keyDict,lock,)))
            p.start()
            process_list.append(p)
        for p in process_list:
            p.join()
        print("Number of data scraped:")
        for key in keyDict.keys():
            print("%s : %s" %(key,keyDict[key]))
    end = time.time()
    print("Total time: %ss" %(round(end - start,2)))

# def showProcess():
#     root = ttk.Window()

def showGUI(allKeys):
    root = ttk.Window()
    root.title("选择要爬取的岗位")
    root.geometry('800x750')
    FrameList=[]
    row =1
    for parentKey in allKeys.keys():
        frame = myCls.Frame(root,row,parentKey,allKeys[parentKey])
        frame.packKeys()
        FrameList.append(frame)
        row += 1
    #function binded to 'OK' button
    def getChoosen():
        choosenList = []
        for frame in FrameList:
            choosenList += (frame.ChoosenKeys())
        root.quit()
        NumofKey = {}
        for key in choosenList:
            NumofKey[key] = 0
        startScraping(NumofKey)

    verifyBtn = ttk.Button(root,text='确定',bootstyle='warning',command=getChoosen)
    verifyBtn.grid(rowspan=2,columnspan=2,column=10,sticky='e')
    
    root.mainloop()

def main():
    url = 'https://www.shixiseng.com'
    allKeys = myCls.KeyPage(url,'').getKey()
    showGUI(allKeys)
   
if __name__ == '__main__':
    main()

