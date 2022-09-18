import requests
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
import scrapingGUI as gui

# scrape page and print log and error messages
def scrape_page(url,page='',keyword='',params=''):
    print('Scraping %s... %sPage%s' %(url,keyword,page))
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.27'
        }
    try:
        response = requests.get(url,params=params,headers=headers)
        if response.status_code == 200:
            html = etree.HTML(response.text)
            return html
        print('Error:get invalid respone %s' %(response.status_code))
    except requests.RequestException:
        print('Error occurred while scraping %s' %(url))

# scrape page of intern job list
def scrape_listPage(page,keyword):
    url = 'https://www.shixiseng.com/interns'
    params = {
        'page': 'page',
        'keyword': keyword,
        'city': '上海'
        }
    html = scrape_page(url,page,keyword,params)
    urlList = html.xpath('//div[@class="f-l intern-detail__job"]//a/@href')
    if page == 1:
        # get the max page number at the first scraping
        last_page = html.xpath('//ul[@class="el-pager"]//li[last()]/text()')[0]
        return urlList,int(last_page)
    else:
        return urlList

# scrape page of detailed information 
# defined as coroutine object to improve efficiency
async def scrape_infoPage(url,dataList):
    async with aiohttp.ClientSession() as session:
        async with await session.get(url) as response:
            html = etree.HTML(await response.text())
            job_name = html.xpath('//div[@class="new_job_name"]/span/text()')[0]
            job_salary = html.xpath('//span[@class="job_money cutom_font"]/text()')[0]
            job_week = html.xpath('//span[@class="job_week cutom_font"]/text()')[0]
            job_time = html.xpath('//span[@class="job_time cutom_font"]/text()')[0]
            job_details = html.xpath('//div[@class="job_detail"]/*/text()')
            job_location = html.xpath('//span[@class="com_position"]/text()')
            # job_location = html.xpath('//div[@class="con-job job_city"]/span[1]/text()')
            com_name = html.xpath('//a[@class="com-name"]/text()')
            com_desc = html.xpath('string(//a[@class="com-name"]/following-sibling::div)')
            save_jobData(job_name,job_salary,job_week,job_time,job_details,
                        job_location,com_name,com_desc,dataList)

# save the job information scraped to a List
def save_jobData(job_name,job_salary,job_week,job_time,job_details,
                job_location,com_name,com_desc,dataList):
    jobData = {
        'job_name': job_name,
        'job_salary': job_salary,
        'job_week': job_week,
        'job_time': job_time,
        # eliminating the '\n''\t' among the information and removing blank
        'job_details': ''.join([deta for deta in [re.sub('\\s', '',detail) 
                       for detail in job_details] if deta != '']),
        'job_location': job_location,
        # aviod out of range error
        'com_name': re.sub('\\s','',''.join(com_name)),
        'com_desc': com_desc,
    }
    dataList.append(jobData)

def scrape_keyPage():
    url = 'https://www.shixiseng.com'
    response = requests.get(url)
    html = etree.HTML(response.text)
    keyDiv = html.xpath('//div[@class="catergories"]//div[5]//div//div')
    keyDict = {}
    for div in keyDiv:
        keyText = div.xpath('.//a/text()')
        keyDict[keyText[0]] = keyText[1:]
    return keyDict


# def print(infoList,s):
#     if len(infoList) < 10:
#         infoList.append(s)
#     else:
#         infoList = infoList[1:-1].append(s)
#     return infoList
#     # for info in infoList:
    #     infoText = ttk.Label(frame,text=info,anchor='w')
    #     infoText.grid()
    
def scrapeBykey(keyword,NumofData,lock):
    #scrape the first page
    page = 1
    urlList,last_page = scrape_listPage(page,keyword)
    #while the number of page is more than 1,continue scraping
    while (page < last_page ):
        page += 1
        urlList.extend(scrape_listPage(page,keyword))
    print("Scraping detailed information...%s" %keyword)
    dataList = []
    loop = asyncio.get_event_loop()
    tasks = [asyncio.ensure_future(scrape_infoPage(url,dataList)) for url in urlList]
    loop.run_until_complete(asyncio.wait(tasks))
    #save data to jobData.csv
    print("Saving Data...%s\n" %(keyword))
    df = pd.DataFrame(dataList)
    df.index += 1
    df.to_csv("{0}_{1}.csv".format(keyword,"实习数据"),encoding="utf-8-sig")
    # with open('jobData_test.json', 'a+',encoding='utf-8') as f:
    #    f.write(json.dumps(dataList,indent=4,ensure_ascii=False))
    with lock:
        NumofData[keyword] = len(urlList)

def scrape_start(keyList):
    start = time.time()
    keyDict = {}
    for key in keyList:
        keyDict[key] =0
    process_list = []
    '''sharing NumofData using manager to save number of data 
    that scraped in different processing'''
    lock = Lock()
    with Manager() as m:
        NumofData = m.dict(keyDict)
        for key in NumofData.keys():
            p = multiprocessing.Process(target=scrapeBykey,args=(key,NumofData,lock,))
            p.start()
            process_list.append(p)
        for p in process_list:
            p.join()
        print("Number of data scraped:")
        for key in NumofData.keys():
            print("%s : %s" %(key,NumofData[key]))
    end = time.time()
    print("Total time: %ss" %(round(end - start,2)))

def showProcess():
    root = ttk.Window()

def main():
    root = ttk.Window()
    root.title("选择要爬取的岗位")
    root.geometry('800x750')
    keyDict = scrape_keyPage()
    FrameList=[]
    row =1
    for name in keyDict.keys():
        frame = gui.Frame(root,row,name,keyDict[name])
        frame.packKeys()
        FrameList.append(frame)
        row += 1
    
    # infoFrame = ttk.Labelframe(root,text='爬取进度',labelanchor='nw',
    #                 width=1000,bootstyle='info')
    # infoFrame.grid(row=row,rowspan=10,columnspan=100,sticky='w')
    # infohead = ttk.Label(infoFrame,text="正在拼命爬取...")
    # infohead.grid()

    def getChoosen():
        choosenList = []
        for frame in FrameList:
            choosenList += (frame.ChoosenKeys())
        root.quit()
        scrape_start(choosenList)

    verifyBtn = ttk.Button(root,text='确定',bootstyle='warning',command=getChoosen)
    verifyBtn.grid(rowspan=2,columnspan=2,column=10,sticky='e')
    
    root.mainloop()
   
if __name__ == '__main__':
    main()

