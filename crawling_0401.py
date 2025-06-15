import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import re
import time
from datetime import datetime
import argparse


# parser = argparse.ArgumentParser(description="處理不同的參數")
# parser.add_argument('--param', type=str, required=True, help="指定參數")
# args = parser.parse_args()
# param = args.param


kw = '10-K'
download_dir = f'C:/{kw}'
os.makedirs(download_dir, exist_ok=True)


options = webdriver.ChromeOptions()
options.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=options)

def crawl_chrome(page, url):
    driver.get(url)
    #time.sleep(2)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Referer': 'https://www.sec.gov',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    max_retries = 3
    retry_count = 0
    wait_time = 60
   
    while retry_count < max_retries:
        try:
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table"))
            )
            break  # 如果找到了元素就跳出循環
        except Exception as e:
            print(f"An error occurred while waiting for the page to load (Attempt {retry_count+1}/{max_retries}):", e)
            retry_count += 1
            time.sleep(3)            
    else:
        print("Failed to load the page after multiple attempts.")
        time.sleep(15)
        try:
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table"))
            )
        except Exception as e:
            print(f"An error occurred while waiting for the page to load (Attempt {retry_count+1}/{max_retries}):", e)
            driver.quit()
            return 0

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    data = soup.select('table')[-1]

    rows = data.find('tbody').find_all('tr')
    domain_download = 'https://www.sec.gov/Archives/edgar/data/'

    if page == 1:
        try:
            no_results_div = soup.find('div', id='no-results-grid', class_='row mt-3 mb-4')
            style = no_results_div.get('style', '')
            time.sleep(6)
            if 'display: none;' in style:
                result_div = soup.find('div', id='show-result-count', role='alert', class_='mb-4')
                result_text = result_div.find('h5').get_text()
                num_kw = re.search(r'[\d,]+', result_text).group()
                num_kw = int(num_kw.replace(',', ''))
                print(num_kw)
            else:
                num_kw = 0
                print("No results found for your search!")
                return num_kw
        except:
            num_kw = 0
            print("Cannot find num of kws.")
            return num_kw

    fail_to_download = []
    success = []
    for row in rows:
        filetype = row.find('td', class_='filetype').getText().strip()
        date = row.find('td', class_='enddate').getText().strip()
        cik = row.find('td', class_='cik d-none').getText().strip().replace(' ', '_').replace('CIK_', '')
        cik_for_url = cik.split('_')[0]

        links = row.find_all('a', attrs={'data-adsh': True})
        for link in links:
            time.sleep(0.3)
            data_adsh = link.get('data-adsh', '')
            data_adsh_cleaned = data_adsh.replace('-', '')

            download_url = domain_download + cik_for_url + '/' + data_adsh_cleaned + '/' + data_adsh + '.txt'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 YaBrowser/22.11.5.715 Yowser/2.5 Safari/537.36',
                'Referer': 'https://www.sec.gov',
                'Accept-Encoding': 'gzip, deflate',
                'Host': 'www.sec.gov'
            }
            response = requests.get(download_url, headers=headers)

            def find_match():
                web_content = response.text
                if 'div style' in web_content.lower() or '</body>' in web_content.lower():
                    file_extension = 'htm'
                else:
                    file_extension = 'txt'
                pattern = re.compile(r'COMPANY CONFORMED NAME:\s*(.*?)\s*CENTRAL INDEX KEY:\s*(\d+)', re.DOTALL)
                match = pattern.search(web_content)
                return match, file_extension, response

            match, file_extension, response = find_match()
            if match:
                central_company = match.group(1).strip().replace('\\', '')
                central_index_key = match.group(2).strip().replace('\\', '')
            else:
                s = requests.Session()
                headers = {
                    'User-Agent': s.headers['User-Agent'],
                    'Referer': 'https://www.sec.gov',
                    'Accept-Encoding': 'gzip, deflate',
                    'Host': 'www.sec.gov'
                }

                response = requests.get(download_url, headers=headers)
                match, file_extension, response = find_match()
                if match:
                    central_company = match.group(1).strip().replace('\\', '')
                    central_index_key = match.group(2).strip().replace('\\', '')
                else:
                    fail_to_download.insert(0, download_url)
                    break

            # if ('10-Q/A' in filetype) or ('10-QA' in filetype):
            #     filename = f"{central_index_key}_{central_company}_10QA_{date}".replace('/', '_').replace(',', '').replace('.', '')
            #     file_with_ext = f"{filename}.{file_extension}"
            # else:
            #     filename = f"{central_index_key}_{central_company}_10Q_{date}".replace('/', '_').replace(',', '').replace('.', '')
            #     file_with_ext = f"{filename}.{file_extension}"
            filename = f"{central_index_key}_{central_company}_{kw}_{date}".replace('/', '_').replace(',', '').replace('.', '')
            file_with_ext = f"{filename}.{file_extension}"

            if response.status_code == 200:
                file_path = os.path.join(download_dir, file_with_ext)
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                    success.insert(0, len(links))
            else:
                fail_to_download.append(filename)

    print(f'p.{page}')
    if page == 1:
        return num_kw

def define_period(beginy, beginm, endy, endm, endd):
    print('begin:',beginy, beginm, 'end:', endy, endm, endd)
    url1 = f'https://www.sec.gov/edgar/search/#/q=the&dateRange=custom&ciks=0000091419&entityName=J%2520M%2520SMUCKER%2520Co%2520(SJM)%2520(CIK%25200000091419)&startdt={beginy}-{beginm}-01&enddt={endy}-{endm}-{endd}&filter_forms={kw}'
    #url1 = f'https://www.sec.gov/edgar/search/#/q=the&dateRange=custom&startdt={beginy}-{beginm}-01&enddt={endy}-{endm}-{endd}&filter_forms={kw}'
    num_kw = int(crawl_chrome(1, url1))
    if num_kw > 100:
        page_goal = (num_kw // 100) + 1
        for next_page in range(2, page_goal + 1, 1):
            crawl_chrome(next_page, f'{url1}&page={next_page}')


# periods = ['2001','01','2024','06']
# for year in range(2004,2025,1):
#     if year == 2004:
#         for month in ["04","07","10"]:
#             periods.append(year)
#             periods.append(month)
        
#     elif 2004< year and year < 2024:
#         for month in ["01","04","07","10"]:
#             periods.append(year)
#             periods.append(month)
#     else:
#         for month in ["01","04","06"]:
#             periods.append(year)
#             periods.append(month)

# for i in range(0,len(periods)-2,2):
#     beginy = periods[i]
#     beginm = periods[i+1]
#     endy = periods[i+2]
#     endm = periods[i+3]
#     define_period(beginy, beginm, endy, endm, "01")

define_period("2023", "01", "2024", "12", "31")

driver.quit()
