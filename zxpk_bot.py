import sys
import time
import requests
from bs4 import BeautifulSoup
import telebot
import logging

NO_NEW_THEMES_MAX_COUNT = 5
REQUESTS_TIMEOUT = 2
NO_NEW_THEMES_TIMEOUT = 60
REQUEST_ERROR_TIMEOUT = 60

TOKEN = ''
CHANEL_NAME = '@oldHW'

url_template = 'http://zx-pk.com/forum/viewtopic.php?t='
url_params = ''

bot = telebot.TeleBot(TOKEN)

navigation_black_list = ['Литература','Новодел','Обсуждения','Куплю','Услуги']
theme_black_list = ['украина','реле']


def has_id(tag):
    return tag.has_attr('id')


def main_process():

    start_theme_id = 8922
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
                theme_title = soup.title.string.replace("- Барахолка ZX-PK.ru","").strip()
                # print(theme_title)
                logging.info("Title: " + theme_title)

                nav_list = soup.find_all('ul', {'class': 'nav-breadcrumbs'})
                forum_list = nav_list[0].find_all('span', {'class': 'crumb'})
                navigation_string = ""
                k=2
                while k < len(forum_list):
                    navigation_string += forum_list[k].get_text()
                    if k != len(forum_list) - 1 : navigation_string += "->"
                    k += 1
                # detect blacklist by forum name
                decision = ""
                for item in navigation_black_list:
                    if navigation_string.find(item) != -1:
                        decision += "reject(forum); "
                        break
                for item in theme_black_list:
                    if theme_title.lower().find(item) != -1:
                        decision += "reject(title); "
                        break
                if len(decision) == 0:
                    post_content = soup.find_all('div', {'class': 'content'})[0]
                    href_list = post_content.find_all('a')
                    k = 0
                    while k < len(href_list):
                        tag = post_content.a
                        tag.extract()
                        k += 1

                    # get photo links
                    photo_links = ""
                    for link in href_list:
                        photo_links += link['href'] + "\n"

                    message_text = navigation_string + "\n" + theme_title + "\n" + post_content.get_text().replace("\n\n", "\n").strip() + \
                                   "\n" + photo_links.strip() + "\n\n" + url
                    print(message_text)
                    try:
                        bot.send_message(CHANEL_NAME, message_text)
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
    return


if __name__ == '__main__':
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s', level=logging.INFO,
                        filename='hwbot_log.log', datefmt='%d.%m.%Y %H:%M:%S')

    main_process()

    logging.info('[App] Script exited.\n')

