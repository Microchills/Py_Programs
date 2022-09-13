import requests
import logging
from lxml import etree
import asyncio
import aiohttp
import time
import json
import re
import pandas as pd

# scrape page and print log and error messages
def scrape_page(url,page,params=''):
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

    logging.info('Scraping %s...',url+'   Page'+str(page))
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.27'
        }
    try:
        response = requests.get(url,params=params,headers=headers)
        if response.status_code == 200:
            html = etree.HTML(response.text)
            return html
        logging.error('get invalid response: %s', response.status_code)
    except requests.RequestException:
        logging.error('error occurred while scraping %s', url)

# save the job information scraped to JSON file
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
    # with open('jobData.txt', 'a+',encoding='utf-8',) as f:
    #     f.write(json.dumps(jobData,indent=4,ensure_ascii=False))
    #     f.write(',' + '\n')

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

# scrape page of intern job list
def scrape_listPage(page):
    url = 'https://www.shixiseng.com/interns'
    params = {
        'page': 'page',
        'keyword': '证券',
        'city': '上海'
        }
    html = scrape_page(url,page,params)
    urlList = html.xpath('//div[@class="f-l intern-detail__job"]//a/@href')
    if page == 1:
        # get the max page number at the first scraping
        last_page = html.xpath('//ul[@class="el-pager"]//li[last()]/text()')[0]
        return urlList,int(last_page)
    else:
        return urlList

    
def main():
    start = time.time()
    #scrape the first page
    page = 1
    urlList,last_page = scrape_listPage(page)
    #while the number of page is more than 1,continue scraping
    while (page < last_page ):
        page += 1
        urlList.extend(scrape_listPage(page))
    print("Scraping detailed information...")
    dataList = []
    loop = asyncio.get_event_loop()
    tasks = [asyncio.ensure_future(scrape_infoPage(url,dataList)) for url in urlList]
    loop.run_until_complete(asyncio.wait(tasks))
    #save data to jobData.csv
    df = pd.DataFrame(dataList)
    df.index += 1
    df.to_csv("jobData.csv",encoding="utf-8-sig")
    # with open('jobData_test.json', 'a+',encoding='utf-8') as f:
    #    f.write(json.dumps(dataList,indent=4,ensure_ascii=False))
    end = time.time()
    print("Number of data scraped: ",len(urlList))
    print("Cost time: ", end - start)

if __name__ == '__main__':
    main()

