# version 1.1 2017-11-25
# @Author Michael Pavlov
# mr.michael.pavlov@gmail.com

import time
import requests
from bs4 import BeautifulSoup
import telebot
import logging

TOKEN = ''
CHANEL_NAME = '@oldHW'

NO_NEW_THEMES_MAX_COUNT = 10
REQUESTS_TIMEOUT = 2
NO_NEW_THEMES_TIMEOUT = 60
REQUEST_ERROR_TIMEOUT = 60

theme_black_list = ['украина','киев','интересные лоты','куплю','ищется','логистика','отзывы']

url_template = 'http://www.phantom.sannata.ru/forum/index.php?t='
url_params = '&st=0'

bot = telebot.TeleBot(TOKEN)


def has_id(tag):
    return tag.has_attr('id')


def main_process():

    start_theme_id = 27608
    last_exist_theme_id = start_theme_id
    current_theme_id = start_theme_id

    while True:
        time.sleep(REQUESTS_TIMEOUT)
        url = url_template + str(current_theme_id) + url_params
        logging.info("URL: " + url)
        print(url)

        try:
            r = requests.get(url)

            if r.status_code == 200:
                last_exist_theme_id = current_theme_id
                soup = BeautifulSoup(r.content, "lxml")
                topic_name = soup.title.string
                print(topic_name)
                logging.info("Title: " + topic_name)

                if topic_name.lower().find('прода') != -1:
                    decision = ""
                    topic_name = topic_name[:topic_name.find(" ::")].strip()
                    for item in theme_black_list:
                        if topic_name.lower().find(item) != -1:
                            decision += "reject(name);"
                            print(decision)
                            logging.info(decision)
                            break
                    if len(decision) == 0:
                        post_list = soup.find_all('td', {'class': 'postentry'})
                        print("sale! do parse...")
                        logging.info("sale! do parse...")
                        # print(post_list[1].find(has_id).get_text("\n"))
                        message_text = "Полигон Призраков:\n" + topic_name + "\n" + post_list[1].find(has_id).get_text("\n").replace(" \n","\n").replace("\n\n","").strip() + "\n\n" + url
                        try:
                            bot.send_message(CHANEL_NAME, message_text)
                            print(message_text)
                            logging.info("SEND:" + message_text)
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

