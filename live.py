import requests
import json
import mysql.connector
import re
from mysql.connector import Error
from scrapy import Selector

url = 'https://focustaiwan.tw/cna2019api/cna/FTNewsList/'


def connect():
    try:
        mydb = mysql.connector.connect(
            host="cmrlabs.com",
            user="cmrlabs_admin",
            passwd="555@ytrewQ",
            database="cmrlabs_news"
        )
        return mydb
    except Error as e:
        print(e)


def cleanhtml(raw_html):
    cleanr = re.compile('<[^p>]+>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def dublicate_control(clone_id):
    mydb = connect()
    mycursor = mydb.cursor()
    sql = "SELECT * FROM tbl_news WHERE clone_id = '" + clone_id + "'"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    if len(myresult) > 0:
        return 1
    else:
        return 0


def fetchNews(page, category):
    data = {
        'category': category,
        'pageidx': page,
        'pagesize': 10,
        'type': 'simple'
    }

    response = requests.post(url, data)

    content = response.json()

    return content['ResultData'][0]['Value']['NewsItems']

    # news['Id']


def is_url_image(image_url):
    image_formats = ("image/png", "image/jpeg", "image/jpg")
    r = requests.head(image_url)
    if r.headers["content-type"] in image_formats:
        return True
    return False


categories = ['politics', 'cross-strait',
              'business', 'society', 'sports', 'sci-tech', 'culture', 'video']
cat_ids = [1, 2, 3, 4, 5, 6, 7, 8]

start_page = 0
finish_page = 2
category = 'news'

for page in range(start_page, finish_page+1):
    list = fetchNews(page, category)

    mydb = connect()

    for news in list:
        # Duplicate control by Id
        if dublicate_control(news['Id']) == 0:
            news_page = requests.get(
                'https://focustaiwan.tw/' + category + '/' + news['Id']).content
            sel = Selector(text=news_page)

            if category == 'video':
                news_content = sel.css('#jsDesP').get()
            else:
                news_content = sel.css('.PrimarySide .paragraph').get()
            news_content = cleanhtml(news_content)
            mycursor = mydb.cursor()
            image = news['Source']
            video = ''
            if category == 'video':
                video = video_url = sel.css(
                    '#jsVideo source').xpath('@src').get()
            cat_index = categories.index(str(news['ClassName']).lower())
            sql = "INSERT INTO tbl_news (cat_id, news_title, news_date, news_description, news_image, news_url, video_url, clone_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            val = (cat_ids[cat_index], news['HeadLine'].replace('(*#*)', '/'), news['CreateTime'], news_content,
                   image, news['PageUrl'], video, news['Id'])
            mycursor.execute(sql, val)

            mydb.commit()
            print('#' + news['Id'] + ' Inserted..')

        else:
            print('#' + news['Id'] + ' is dublicated.')
