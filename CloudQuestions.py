# -*- coding: utf-8 -*-
# version 1.02 2018-02-14
# @Author Michael Pavlov

import requests
import logging
import telebot
import time
from bs4 import BeautifulSoup
import threading
from queue import Queue
from requests_toolbelt.adapters import source
from datetime import datetime, timedelta
import mysql.connector
from logging.handlers import RotatingFileHandler
import json

# CloudQuestionsBot
TOKEN = '425350274:AAFk8avdWOUdhES4RTVZDJI10NvZdl8ITtg'
bot = telebot.TeleBot(TOKEN)


DB_USER = "bot_user"
DB_PASSWORD = "bot_user==="
DB_HOST = "37.110.112.91"
DB_PORT = "9999"
DB_DATABASE = "bots"

# DB_USER = "bot_user"
# DB_PASSWORD = "bot_user==="
# DB_HOST = "127.0.0.1"
# # DB_HOST = "192.168.1.5"
# DB_PORT = "3306"
# DB_DATABASE = "bots"


# NO_NEW_THEMES_MAX_COUNT = 32
REQUESTS_TIMEOUT = 10
CRAWLER_TIMEOUT = 30
# NO_NEW_THEMES_TIMEOUT = 60
# REQUEST_ERROR_TIMEOUT = 1

headers = {'User-Agent': '''Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36 OPR/49.0.2725.64'''}


@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        logger.info("Receive Start command from chat ID:" + str(message.chat.id))
        for result_ in cursor_m.execute("SELECT qbot_users.id FROM qbot_users WHERE id=%s", (message.chat.id,), multi=True):
            pass
        if len(cursor_m.fetchall()) > 0:
            # user exist
            for result_ in cursor_m.execute("SELECT * FROM qbot_users WHERE id=%s", (message.chat.id,), multi=True):
                pass
            user = cursor_m.fetchall()[0]
            bot.send_message(message.chat.id, "welcome back " + str(user[0]))
            if len(user[2]) == 0:
                bot.send_message(message.chat.id, "Your tags list is empty")
            else:
                bot.send_message(message.chat.id, "Your tags list:\n" + str(user[2]).replace("|","\n"))
        else:
            # create new user
            if message.from_user.username is not None:
                add_user(message.from_user.username,message.chat.id)
                logger.info("User with name=" + message.from_user.username + " and ID=" + str(message.chat.id) + " created")
                bot.send_message(message.chat.id, "Your are in. tap /help")
            else:
                add_user(message.from_user.first_name, message.chat.id)
                logger.info("User with name=" + message.from_user.first_name + " and ID=" + str(message.chat.id) + " created")
                bot.send_message(message.chat.id, "Your are in. tap /help")
    except mysql.connector.DatabaseError as err:
        logger.warning("Cant execute Start command. Reconnect..." + str(err))
        if mysql_reconnect():
            return handle_start(message)
        else:
            logger.critical("Cant execute Start command. ")
            bot.send_message(message.chat.id, "FUBAR. We worked on it...")
    except Exception as e:
        logger.critical("Cant execute Start command. " + str(e))
        bot.send_message(message.chat.id, "FUBAR. We worked on it...")
    return

@bot.message_handler(commands=['set'])
def handle_set(message):
    try:
        logger.info("Receive Set command from chat ID:" + str(message.chat.id))
        msg = bot.reply_to(message, "please provide new list..")
        bot.register_next_step_handler(msg, update_list)
    except Exception as e:
        logger.critical("Cant execute Set command. " + str(e))
    return

def update_list(message):
    try:
        logger.info("set list: \n" + message.text.replace("\n","|"))
        if tags_validation(message.text):
            tags = message.text.replace("\n","|").lower()
            set_tags(message.chat.id,tags)
            bot.reply_to(message, "done!")
        else:
            bot.send_message(message.chat.id, "format error, try again..")
            bot.register_next_step_handler(message, update_list)
    except Exception as e:
        logger.critical("Cant Update List. " + str(e))
    return

@bot.message_handler(commands=['show']) # show and edit tag-list
def handle_show(message):
    try:
        logger.info("Receive Show command from chat ID:" + str(message.chat.id))
        # cursor = my_connection.cursor()
        for result_ in cursor_m.execute("SELECT qbot_users.tags FROM qbot_users WHERE id=%s", (message.chat.id,), multi=True):
            pass
        tags = cursor_m.fetchall()[0][0]
        if len(tags) == 0:
            bot.send_message(message.chat.id, "Your tags list is empty")
        else:
            bot.send_message(message.chat.id, tags.replace("|","\n"))
        logger.debug(tags.replace("|","\n"))
    except mysql.connector.DatabaseError as err:
        logger.warning("Cant execute Show command. Reconnect..." + str(err))
        if mysql_reconnect():
            return handle_show(message)
        else:
            logger.critical("Cant execute Show command. ")
            bot.send_message(message.chat.id, "FUBAR. We worked on it...")
    except Exception as e:
        logger.critical("Cant execute Show command. " + str(e))
        bot.send_message(message.chat.id,"FUBAR. We worked on it...")
    return

@bot.message_handler(commands=['clear']) # clear tag-list
def handle_clear(message):
    try:
        set_tags(message.chat.id, "")
        bot.send_message(message.chat.id, "done")
    except Exception as e:
        logger.critical("Cant execute Clear command. " + str(e))
    return

@bot.message_handler(commands=['help'])
def show_help(message):
    try:
        logger.info("Receive Help command from chat ID:" + str(message.chat.id))
        bot.send_message(message.chat.id, "Usage:\n"
                          "/help - show this message\n"
                          "/qq - answer the question\n"
                          "/show - show your questions and answers\n"
                          "/get - get incomming questions\n"                
                          "/... - ...\n"
                          "/clear - delete all questions\n"
                          "\n"
                          "\n", parse_mode='Markdown')
    except Exception as e:
        logger.critical("Cant execute Help command. " + str(e))
    return

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    try:
        bot.send_message(message.chat.id, "done =(")
    except Exception as e:
        logger.critical("Cant execute Stop command. " + str(e))
    return

@bot.message_handler(commands=['addurl']) # add profile url
def handle_add_url(message):
    try:
        logger.info("Receive Add URL command from chat ID:" + str(message.chat.id))
        msg = bot.reply_to(message, "please provide profile URL (vk.com,fb.com, github,com etc)..")
        bot.register_next_step_handler(msg, bot_add_url)
    except Exception as e:
        logger.critical("Cant execute Add URL command. " + str(e))
    return

def bot_add_url(message):
    try:
        logger.info("Add URL: \n" + message.text.replace("\n","|"))
        if url_validation(message.text):
            add_url(message.chat.id, message.text, connection_main, cursor_m)
            bot.reply_to(message, "done!")
            bot.register_next_step_handler(message, bot_show_updated_tags)
        else:
            bot.send_message(message.chat.id, "format error, try again..")
            bot.register_next_step_handler(message, bot_add_url)
    except Exception as e:
        logger.critical("Cant add URL. " + str(e))
    return

def add_url(user_id_,url_,connection_, cursor_):

    urls_list = get_urls(user_id_, cursor_)
    if urls_list.count(url_) == 0:
        urls_list.append(url_)
        new_urls_string = "|".join(urls_list)
        try:
            for result_ in cursor_.execute("UPDATE qbot_users SET profile_urls=%s WHERE id=%s", (new_urls_string,user_id_),multi=True):
                pass
        except mysql.connector.DatabaseError as err:
            logger.warning("Cant SET url list for user_id: " + str(user_id_) + ". Reconnect... " + str(err))
            if mysql_reconnect():
                return add_url(user_id_,url_,connection_, cursor_)
            else:
                logger.critical("Cant SET url list for user_id: " + str(user_id_))
                bot.send_message(user_id_, "FUBAR. We worked on it...")
        except Exception as e:
            logger.critical("Cant SET url list for user_id: " + str(user_id_) + ". " + str(e))
        else:
            try:
                connection_.commit()
            except Exception as e:
                logger.critical("Cant commit transaction Set url list for user_id: " + str(user_id_) + ". " + str(e))
    else:
        logger.debug("URL already exist: " + url_)
    return

def get_urls(user_id_, cursor_):

    try:
        for result_ in cursor_.execute("SELECT qbot_users.profile_urls FROM qbot_users WHERE id=%s",(user_id_,), multi=True):
            pass
        result_set = cursor_.fetchall()[0][0]
        if len(result_set) > 0:
            urls_list = result_set.split("|")
        else:
            urls_list = []
        return urls_list
    except mysql.connector.DatabaseError as err:
        logger.warning("Cant GET url list for user_id: " + str(user_id_) + ". Reconnect... " + str(err))
        if mysql_reconnect():
            return get_urls(user_id_, cursor_)
        else:
            logger.critical("Cant GET url list for user_id: " + str(user_id_))
            bot.send_message(user_id_, "FUBAR. We worked on it...")
    except Exception as e:
        logger.critical("Cant GET url list for user_id: " + str(user_id_) + ". " + str(e))

    return

def bot_show_updated_tags(message_):
    # TODO get info from new URL
    # TODO generate updated tag lists
    # TODO show taglist to user and get confirmation and update Profile

    return

# now we can answer to any message, not only commands
@bot.message_handler(func=lambda m: True)
def handle_other_message(message):
    content_ = message.text.strip()
    print(content_)
    if content_.find("?") != -1:
        # it is question!
        print("fine question!")
        bot.reply_to(message, "Question Tags: <random tags>\n Is it correct? OK")
        bot.register_next_step_handler(message, question_processing)
        return
    else:
        logger.info("Unknown command: " + str(message) + ". Show Help")
        show_help(message)
    return

def question_processing(message_):

    #  TODO Question processing: get tags,
    #  TODO manual tag list correction (wished: in real time show users count with the same tags)
    #  TODO commit to DB
    #  TODO add to processing Queue()
    bot.reply_to(message_, "Now sending you Q to people: ")

    return


def worker(thread_id_,connection_,cursor_): # processing Queue(), matching, sending
    logger.debug("#" + str(thread_id_) + " Starting working thread...")
    while True:
        try:
            if not queue.empty():
                item = queue.get() # item[0]:id, item[1]: tags, item[2]: text, item[3+]: additional filters(age,profi,geo)
                for user in get_users(cursor_):  # user[0]:id
                    if question_ok_for_user(item,user[0]):
                        send_item(user[0],item)
                queue.task_done()
            else:
                logger.debug("Queue is empty. Sleep...")
                time.sleep(5)
        except Exception as e:
            logger.critical("Cant Send Notify. " + str(e))
            return

def question_ok_for_user(question_set_, user_id_):
    # question_set (item[0]:id, item[1]: tags, item[2]: text, item[3+]: additional filters(age,profi,geo))

    # TODO Matching function

    return False

def send_item(channel_,item_):
    # item[0]:id, item[1]: tags, item[2]: text, item[3+]: additional filters(age,profi,geo)
    message_text = item_[2] + "\n" + item_[1] # send text and tags
    try:
        bot.send_message(channel_, message_text, disable_web_page_preview=True)
        logger.info("SEND MES:" + message_text.replace("\n", ", "))
    except Exception as err:
        logger.error("Can't send message to channel! Skip. " + str(
            err) + ". Message: " + message_text)
    return

def url_crawler(session_, url_):
    logger.info("Request url : " + url_)
    try:
        r = session_.get(url_, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "lxml")
            if url_.find("facebook.com") != -1:
                fb_parser(soup)
            if  url_.find("vk.com") != -1:
                vk_parser(soup)
            if url_.find("github.com") != -1:
                gh_parser(soup)
            if url_.find("linkedin.com") != -1:
                in_parser(soup)
            if url_.find("habrahabr.ru") != -1:
                habra_parser(soup)
            if url_.find("hh.com") != -1:
                hh_parser(soup)
            if url_.find("superjob.ru") != -1:
                sj_parser(soup)
        else:
            logger.warning("Code: " + str(r.status_code) + " for URL: " + url_)
    except requests.exceptions.RequestException as e:
        logging.error("Request error: " + url_ + str(e))
    except Exception as ex:
        logging.error("Request unknown error. Url: " + url_ + str(ex))
    return

# parsers =====================================
def vk_parser(soup_):

    user_name = ""
    user_age = ""
    user_skillset = []
    user_location = ""
    user_employers_list = []
    user_backgroud_list = []
    user_likes = []
    user_hates = []

    result_set = json.dumps({})

    try:
        logger.debug("Starting parse VK page: ")

    except Exception as e:
        logger.warning("parser exception: " + str(e))
    return result_set

def fb_parser(soup_):
    user_name = ""
    user_age = ""
    user_skillset = []
    user_location = ""
    user_employers_list = []
    user_backgroud_list = []
    user_likes = []
    user_hates = []

    try:
        logger.debug("Starting parse FB page: ")

    except Exception as e:
        logger.warning("parser exception: " + str(e))
    return

def gh_parser(soup_):
    user_name = ""
    user_age = ""
    user_skillset = []
    user_location = ""
    user_employers_list = []
    user_backgroud_list = []
    user_likes = []
    user_hates = []

    try:
        logger.debug("Starting parse GH page: ")

    except Exception as e:
        logger.warning("parser exception: " + str(e))
    return

def in_parser(soup_):
    user_name = ""
    user_age = ""
    user_skillset = []
    user_location = ""
    user_employers_list = []
    user_backgroud_list = []
    user_likes = []
    user_hates = []

    try:
        logger.debug("Starting parse IN page: ")

    except Exception as e:
        logger.warning("parser exception: " + str(e))
    return

def habra_parser(soup_):
    user_name = ""
    user_age = ""
    user_skillset = []
    user_location = ""
    user_employers_list = []
    user_backgroud_list = []
    user_likes = []
    user_hates = []

    try:
        logger.debug("Starting parse IN page: ")

    except Exception as e:
        logger.warning("parser exception: " + str(e))
    return

def hh_parser(soup_):
    user_name = ""
    user_age = ""
    user_skillset = []
    user_location = ""
    user_employers_list = []
    user_backgroud_list = []
    user_likes = []
    user_hates = []

    try:
        logger.debug("Starting parse IN page: ")

    except Exception as e:
        logger.warning("parser exception: " + str(e))
    return

def sj_parser(soup_):
    user_name = ""
    user_age = ""
    user_skillset = []
    user_location = ""
    user_employers_list = []
    user_backgroud_list = []
    user_likes = []
    user_hates = []

    try:
        logger.debug("Starting parse IN page: ")

    except Exception as e:
        logger.warning("parser exception: " + str(e))
    return
# parsers =====================================



def mysql_reconnect():
    try:
        connection_main = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD,
                                            host=DB_HOST, port=DB_PORT,
                                            database=DB_DATABASE)
        connection_w1 = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD,
                                            host=DB_HOST, port=DB_PORT,
                                            database=DB_DATABASE)
        connection_gc = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD,
                                            host=DB_HOST, port=DB_PORT,
                                            database=DB_DATABASE)
        cursor_m = connection_main.cursor()
        cursor_w1 = connection_w1.cursor()
        cursor_gc = connection_gc.cursor()
        logger.info("Reconnect successful")
        return True
    except Exception as e:
        logger.critical("no database connection. exit" + str(e))
        return False

def tags_validation(str_):
    try:
        if str_.find("|") >=0: return False
    except Exception as e:
        logger.critical("Cant validate tags list. " + str(e))
    return True

def url_validation(str_):
    try:
        if str_.find("|") >=0: return False
    except Exception as e:
        logger.critical("Cant validate URL. " + str(e))
    return True

def add_user(name_, chat_id_):
    try:
        for result_ in cursor_m.execute("insert into qbot_users (name,id,tags) values (%s,%s,%s)", (name_, chat_id_, ""), multi=True):
            pass
    except mysql.connector.DatabaseError as err:
        logger.warning("Cant add User. Reconnect..." + str(err))
        if mysql_reconnect():
            return add_user(name_, chat_id_)
        else:
            logger.critical("Cant add User. ")
            bot.send_message(chat_id_, "FUBAR. We worked on it...")
    except Exception as e:
        logger.critical("Cant add User. " + str(e))
    else:
        try:
            connection_main.commit()
        except Exception as e:
            logger.critical("Cant commit transaction Add User. " + str(e))
    return

def set_tags(chat_id_, tags_):
    try:
        # cursor = my_connection.cursor()
        for result_ in cursor_m.execute("UPDATE qbot_users SET tags=%s WHERE id=%s", (tags_, chat_id_), multi=True):
            pass
    except mysql.connector.DatabaseError as err:
        logger.warning("Cant Set tags. Reconnect..." + str(err))
        if mysql_reconnect():
            return set_tags(chat_id_, tags_)
        else:
            logger.critical("Cant Set tags. ")
            bot.send_message(chat_id_, "FUBAR. We worked on it...")
    except Exception as e:
        logger.critical("Cant Set tags. " + str(e))
    else:
        try:
            connection_main.commit()
        except Exception as e:
            logger.critical("Cant commit transaction Set tags. " + str(e))
    return


def start_polling():
    while True:
        try:
            logger.info("Starting polling thread...")
            bot.polling(none_stop=True,timeout=120)
        except Exception as e:
            logger.critical("Cant start Bot polling. " + str(e))
            bot.stop_polling()
            time.sleep(10)
    return

def get_users(cursor_):
    try:
        for result_ in cursor_.execute("SELECT qbot_users.id, qbot_users.tags FROM qbot_users", multi=True):
            pass
        return cursor_.fetchall()
    except mysql.connector.DatabaseError as err:
        logger.warning("Cant Get Users or No User exist. Reconnect..." + str(err))
        if mysql_reconnect():
            return get_users(cursor_)
        else:
            logger.critical("Cant Get Users or No User exist. ")
    except:
        logger.critical("Cant Get Users or No User exist. " + str(e))
        return []





def get_session(bind_ip_="", need_tor_=False):
    try:
        session = requests.Session()
        if need_tor_:
            session.proxies = {'http': 'socks5://127.0.0.1:9051',
                               'https': 'socks5://127.0.0.1:9051'}
        if bind_ip_ != "":
            new_source = source.SourceAddressAdapter(bind_ip_)
            session.mount('http://', new_source)
            session.mount('https://', new_source)
        return session
    except Exception as e:
        logger.critical("Cant get new session for IP: " + str(bind_ip_) + "; " + str(e))



if __name__ == '__main__':

    logger = logging.getLogger("qq_bot")
    logger.setLevel(logging.DEBUG)
    fh = RotatingFileHandler("qq_bot.log", mode='a', encoding='utf-8', backupCount=5, maxBytes=16 * 1024 * 1024)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    try:
        connection_main = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD,
                                            host=DB_HOST, port=DB_PORT,
                                            database=DB_DATABASE)
        connection_w1 = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD,
                                            host=DB_HOST, port=DB_PORT,
                                            database=DB_DATABASE)
        connection_gc = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD,
                                            host=DB_HOST, port=DB_PORT,
                                            database=DB_DATABASE)
        cursor_m = connection_main.cursor()
        cursor_w1 = connection_w1.cursor()
        cursor_gc = connection_gc.cursor()
    except Exception as e:
        print("no database connection. exit")
        logger.critical(e)
        quit()

    queue = Queue()

    # ====== debug area

    # print(get_users(cursor_m))
    # quit()

    # ================


    t_polling = threading.Thread(target=start_polling)
    t_notify = threading.Thread(target=worker, args=(10, connection_w1, cursor_w1))
    # t_crawler_1 = threading.Thread(target=users_crawler, args=('192.168.1.5', 1, cursor_m))

    t_polling.start()
    t_notify.start()
    # t_crawler_1.start()

    t_polling.join()
    t_notify.join()
    # t_crawler_1.join()

    queue.join()

