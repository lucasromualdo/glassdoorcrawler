from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import progressbar
import json
from openpyxl.workbook import Workbook
import re
def get_position_link(url):
    
    '''
    This function has for role to send a request to Glassdoor and crawlers for links which have for class 'jobLink'.
    get_position_links() collects data science applications in every
    page which get_all_link() asks for
    Args:
           url: page URL
    returns: Python list:
            links: all links for job applications present a single page.
    '''
    
    links = []
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url,headers=header)
    soup = BeautifulSoup(response.text, 'html.parser')

    a = soup.find_all('a', class_='jobLink')
    for i in a:
        links.append('https://www.glassdoor.com' + i.get('href'))

    return links


def get_all_links(num_page, url):
    
    link = []
    i = 1
    print('Collecting links....')
    while i <= num_page:
        try:
            url_main = url + str(i) + '.htm'
            link.append(get_position_link(url_main))
            i = i + 1
            time.sleep(0.5)
        except:
            print('No more pages found.')
    return link


def scrap_job_page(url):

    dic = {}
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=header)
    soup = BeautifulSoup(response.text, 'html.parser')
    body = soup.find('body')
    #     print(title)
    #print(body)
    try:
        #         job title
          #body.find('script').text.strip()
        script_text  = body.find('script').get_text()
        relevant = script_text[script_text.index('=')+1:] 
        #removes = and the part before it
        relevante = relevant.rstrip(';')
        data = json.loads(relevante) #a dictionary!
        #print(data)
        dic['job_title']=data['initialState']['jlData']['header']['jobTitleText']
        
        
        
        '''
        for key in data.keys():
          print(key)
        '''
        
    except Exception as e:
        dic['job_title'] = np.nan
        print(e)
    #print(dic['job_title'])
    try:
        # company name
        script_text  = body.find('script').get_text()
        relevant = script_text[script_text.index('=')+1:] 
        relevante = relevant.rstrip(';')
        data = json.loads(relevante) 
        dic['company_name']=data['initialState']['jlData']['header']['employer']['name']
    except:
        dic['company_name'] = np.nan

    try:
        
        script_text  = body.find('script').get_text()
        relevant = script_text[script_text.index('=')+1:] 
        relevante = relevant.rstrip(';')
        data = json.loads(relevante) 
        dic['location']=data['initialState']['jlData']['header']['locationName']
    except:
        dic['location'] = np.nan


    try:
        dic['salary_estimated'] = body.find('h2', class_='salEst').text.strip()
    except:
        dic['salary_estimated'] = np.nan
    try:
        dic['salary_min'] = body.find('div', class_='minor cell alignLt').text.strip()
    except:
        dic['salary_min'] = np.nan
    try:

        dic['salary_max'] = body.find('div', class_='minor cell alignRt').text.strip()
    except:
        dic['salary_max'] = np.nan

    
  
    try:

        script_text  = body.find('script').get_text()
        relevant = script_text[script_text.index('=')+1:] 
        #removes = and the part before it
        relevante = relevant.rstrip(';')
        data = json.loads(relevante) #a dictionary!
        #print(data)
        dic['job_description']=data['initialState']['jlData']['job']['description']

        
    except:
        dic['job_description'] = np.nan

    return dic


if __name__ == '__main__':
    
    #This link is aimed to start scraping data science jobs. If you would like to scarp data related to another type of job,
    #you should then copy the link of the desired type of job (i.e, Software engineering) from glassdoor and past the link
    #into get_all_links() function.
    #30 is the number of pages. There are around 60 positions in every page.
    links = get_all_links(1, 'https://www.glassdoor.com.br/Vaga/belo-horizonte-desenvolvedor-vagas-SRCH_IL.0,14_IC2514646_KO15,28.htm')
    flatten = [item for sublist in links for item in sublist]
    # The scraper may crawl duplicate links
    remove_duplicates = list(set(flatten))
    #UI progress bar
    bar = progressbar.ProgressBar(maxval=len(remove_duplicates), \
                                  widgets=['Crawling the site: ', progressbar.Bar('=', '[', ']'), ' ',
                                           progressbar.Percentage()]).start()
    list_result = []

    for page in remove_duplicates:
        bar.update(remove_duplicates.index(page))
        try:
            list_result.append(scrap_job_page(page))
        except:
            pass
        time.sleep(0.5)
    #Save the dictionary into a dataframe
    df_glass = pd.DataFrame.from_dict(list_result)
    #The program will create an Excel file named data_glassdoor in the same directory as this script 
    writer = pd.ExcelWriter('belohorizonte_vagas.xlsx', engine='openpyxl')
    #Writing data into the Excel file
    df_glass.to_excel(writer, index=False)
    df_glass.to_excel(writer, startrow=len(df_glass) + 2, index=False)
    writer.save()