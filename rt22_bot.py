# -*- coding: utf-8 -*-

import sys
import time
import requests
from bs4 import BeautifulSoup
import telebot
import logging
from bs4 import UnicodeDammit

NO_NEW_THEMES_MAX_COUNT = 10
REQUESTS_TIMEOUT = 1
NO_NEW_THEMES_TIMEOUT = 60
REQUEST_ERROR_TIMEOUT = 60

TOKEN = '504713240:AAH881_7VXN0fhNTDsfGL_bvJ-R0FcZ3C8I'
CHANEL_NAME = '@oldHW'

forum =  "http://rt22.ru/"
url_template = "http://rt22.ru/viewtopic.php?t="
url_params = ''
login = "mixey"
password = "1111111"
headers = {'User-Agent': 'Mozilla/5.0'}
payload = {'username': login, 'password': password, 'redirect': 'index.php', 'sid': '', 'login': 'Login'}

bot = telebot.TeleBot(TOKEN)

navigation_white_list = ['Имею','Отдам', 'Компьютерное','Разное']
theme_black_list = ['украина','реле']


def main_process():

    session = requests.Session()
    r = session.post(forum + "ucp.php?mode=login", headers=headers, data=payload)
    if r.text.find("Выход [ mixey ]") != -1:
        print("Login successful")
    else:
        print("Error while login")
        exit(-1)

    start_theme_id = 58447
    last_exist_theme_id = start_theme_id
    current_theme_id = start_theme_id

    while True:
        time.sleep(REQUESTS_TIMEOUT)
        url = url_template + str(current_theme_id) + url_params
        logging.info("URL: " + url)
        print(url)

        try:
            r = session.get(url)
            # r.encoding = 'utf-8'

            if r.status_code == 200:
                last_exist_theme_id = current_theme_id
                soup = BeautifulSoup(r.text, "lxml")
                theme_title = soup.title.string.replace("RT22.RU Радиотехника 20 века, форумы • Просмотр темы - ","").strip()
                # print(theme_title)

                nav_list = soup.find_all('p', {'class': 'breadcrumbs'})
                navigation_string = nav_list[0].get_text().replace("Портал » Список форумов » ","").strip()
                # print(navigation_string)

                # detect whitelist by forum name
                decision = "reject(forum);"
                for item in navigation_white_list:
                    if navigation_string.find(item) != -1:
                        decision = ""
                        break
                for item in theme_black_list:
                    if theme_title.lower().find(item) != -1:
                        decision += "reject(title); "
                        break
                print(decision)
                if len(decision) == 0:
                    post_content = soup.find_all('div', {'class': 'postbody'})
                    post_message = post_content[0].get_text("\n").replace(" \n","\n").replace("\n\n", "\n").strip()[0:950]

                    href_list = post_content[0].find_all('a')
                    k = 0
                    while k < len(href_list):
                        tag = post_content[0].a
                        tag.extract()
                        k += 1

                    # get photo links
                    k = 0
                    photo_links = ""
                    for link in href_list:
                        photo_links += link['href'] + "\n"
                        if k > 8: break
                        k += 1
                    message_text = navigation_string + "\n" + theme_title + "\n" + post_message + \
                                   "\n" + photo_links.strip() + "\n\n" + url
                    try:
                        bot.send_message(CHANEL_NAME, message_text)
                        print(message_text)
                    except Exception as e:
                        logging.error("Can't send to channel!")
                        logging.error(e)

                print("=====================")
            else:
                logging.info("Code: " + str(r.status_code))
                print(r.status_code)
                if current_theme_id - last_exist_theme_id > NO_NEW_THEMES_MAX_COUNT:
                    print("no new themes. going to sleep(" + str(NO_NEW_THEMES_TIMEOUT) + ") sec...")
                    logging.info("no new themes. going to sleep(" + str(NO_NEW_THEMES_TIMEOUT) + ") sec...")
                    current_theme_id = last_exist_theme_id
                    time.sleep(NO_NEW_THEMES_TIMEOUT)
                print("=====================")
            current_theme_id += 1

        except requests.exceptions.RequestException as e:
            logging.error("error. going to sleep(" + str(REQUEST_ERROR_TIMEOUT) + ") sec...")
            logging.error(e)
            print("error. going to sleep(" + str(REQUEST_ERROR_TIMEOUT) + ") sec...")
            print(e)
            time.sleep(REQUEST_ERROR_TIMEOUT)
        except Exception as ex:
            logging.error("unknown error. going to next url...")
            logging.error(ex)
            print("error. going to going to next url...")
            print(ex)
            last_exist_theme_id = current_theme_id
            current_theme_id += 1
    return


if __name__ == '__main__':
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s', level=logging.INFO,
                        filename='hwbot_log.log', datefmt='%d.%m.%Y %H:%M:%S')

    main_process()

    logging.info('[App] Script exited.\n')

