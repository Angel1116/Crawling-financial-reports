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

#download_dir = 'D:'
download_dir = '10Q_with_10QA'
os.makedirs(download_dir, exist_ok=True)

df = pd.read_csv('combined_list.csv')
combined_list = df['Items'].tolist()

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
            break  
        except Exception as e:
            print(f"An error occurred while waiting for the page to load (Attempt {retry_count+1}/{max_retries}):", e)
            retry_count += 1
            time.sleep(3)
    else:
        print("Failed to load the page after multiple attempts.")
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
            if 'display: none;' in style:
                result_div = soup.find('div', id='show-result-count', role='alert', class_='mb-4')
                result_text = result_div.find('h5').get_text()
                num_10q = re.search(r'[\d,]+', result_text).group()
                num_10q = int(num_10q.replace(',', ''))
                print(num_10q)
            else:
                num_10q = 0
                print("No results found for your search!")
                return num_10q
        except:
            num_10q = 0
            print("Cannot find num of 10qs.")
            return num_10q

    fail_to_download = []
    success = []
    for row in rows:
        filetype = row.find('td', class_='filetype').getText().strip()
        date = row.find('td', class_='enddate').getText().strip()
        cik = row.find('td', class_='cik d-none').getText().strip().replace(' ', '_').replace('CIK_', '')
        cik_for_url = cik.split('_')[0]

        links = row.find_all('a', attrs={'data-adsh': True})
        for link in links:
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

            if ('10-Q/A' in filetype) or ('10-QA' in filetype):
                filename = f"{central_index_key}_{central_company}_10QA_{date}".replace('/', '_').replace(',', '').replace('.', '')
                file_with_ext = f"{filename}.{file_extension}"
            else:
                filename = f"{central_index_key}_{central_company}_10Q_{date}".replace('/', '_').replace(',', '').replace('.', '')
                file_with_ext = f"{filename}.{file_extension}"

            if response.status_code == 200:
                file_path = os.path.join(download_dir, file_with_ext)
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                    success.insert(0, len(links))
            else:
                fail_to_download.append(filename)

    print("------------------")
    print(f'p.{page}')
    print("O: ", len(success))
    print("X: ", len(fail_to_download))
    if page == 1:
        return num_10q


for firm_index in range(5973,len(combined_list), 1):  
    firm = combined_list[firm_index]
    print(firm_index, firm)

    firm = firm.replace('&', '%2526').replace('/', '%252F').replace(' ', '%2520')
    url1 = f'https://www.sec.gov/edgar/search/#/q=the&dateRange=custom&entityName={firm}&startdt=2001-01-01&enddt=2024-06-24&filter_forms=10-Q'

    num_10q = int(crawl_chrome(1, url1))
    if num_10q > 100:
        page_goal = (num_10q // 100) + 1
        for next_page in range(2, page_goal + 1, 1):
            crawl_chrome(next_page, f'{url1}&page={next_page}')

driver.quit()
