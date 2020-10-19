import telegram
import logging
import pandas as pd
import json
import datetime
import urllib.request

import schedule,time

import datetime
import pytz
from pytz import timezone

import smtplib


telegram_token = {YOUR TOKEN}

# Valid stock ticker list
sp = pd.read_csv('source_code/data.csv')
allTicker_list = sp['ticker'].values.tolist()
# Initialize
valid_list = []
#initialize

# Initialize

valid_news = []
user_data={}



from telegram import ReplyKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler,PicklePersistence)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename="info.log",
                    level=logging.INFO)

logger = logging.getLogger(__name__)

SUBSCRIBE, ENTER_TICKER, EDIT, BACK_TO_STEP_1, FEEDBACK, ALERTING= range(6)

reply_keyboard = [['Subscribe','My Subscription'],['Feedback','Join Waitlist']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data_new):
    facts = list()

    for key, value in user_data_new.items():
        facts.append('{} : {}'.format('\N{cheering megaphone}', key))

    return "\n".join(facts).join(['\n', '\n'])

def start(update,context):
    update.message.reply_text(
        'Hello. Welcome to Stock News Alert. You can choose between:',
        reply_markup = markup
    )
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    if first_name is None:
        first_name = 'N/A'
    last_name = update.message.chat.last_name
    if last_name is None:
        last_name = 'N/A'
    # Convert userTime into string
    userTime= update.message.date
    # userTime= datetime.datetime.fromtimestamp(userTime)
    userTime= userTime.strftime('%Y-%m-%d %H:%M:%S')
    content = update.message.text
    if content is None:
        content = 'N/A'

    try:
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()

        new_job = context.job_queue.run_repeating(make_alert,30,context=chat_id)

        #UTC 19:00
        eastern = timezone('US/Eastern')
        t = datetime.time(14,30,00,0000, tzinfo=eastern)
        daily_job = context.job_queue.run_daily(daily_top_mention,t,days=(0,1,2,3,4,5,6),context=chat_id)

        t1 = datetime.time(19,5,00,0000,tzinfo=eastern)
        weekly_job = context.job_queue.run_daily(weekly_top_mention,t1,days=(5),context=chat_id)

        t2 = datetime.time(0,10,00,0000)
        monthly_job = context.job_queue.run_daily(monthly_top_mention,t2,days=(0,1,2,3,4,5,6),context=chat_id)
        context.chat_data['job'] = [new_job,daily_job,weekly_job,monthly_job]
        #context.chat_data['job'] = [new_job,daily_job]
        update.message.reply_text('News alerts successfully set!')

    except:
        #update.message.reply_text("An error has occured setting up the news alerts")
        pass
    return SUBSCRIBE

def subscribe(update, context):
    if len(valid_list)<3:
        num = 3-len(valid_list)
        update.message.reply_text(
            "Please enter up to "+str(num)+' valid stock ticker(s) Seperate with ,')
        chat_id = update.message.chat_id
        first_name = update.message.chat.first_name
        if first_name is None:
            first_name = 'N/A'
        last_name = update.message.chat.last_name
        if last_name is None:
            last_name = 'N/A'
        # Convert userTime into string
        userTime= update.message.date
        # userTime= datetime.datetime.fromtimestamp(userTime)
        userTime= userTime.strftime('%Y-%m-%d %H:%M:%S')
        content = update.message.text
        if content is None:
            content = 'N/A'

        return ENTER_TICKER
    else:
        update.message.reply_text(
            'You have subscribed to the news alert of:\n\N{pushpin} '+'\n\N{pushpin} '.join(valid_list)+"\n reaching the limit of your current plan \N{disappointed face}"
            "\nIf you wish gain unlimited access, let us know by pressing 'Join Waitlist' \N{chart with upwards trend}"
            "\nIf you wish to change the current subscription list, press 'My Subscription'",
            reply_markup=markup
        )
        try:
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()

            new_job = context.job_queue.run_repeating(make_alert,30,context=chat_id)

            #UTC 19:00
            eastern = timezone('US/Eastern')
            t = datetime.time(14,30,00,0000, tzinfo=eastern)
            daily_job = context.job_queue.run_daily(daily_top_mention,t,days=(0,1,2,3,4,5,6),context=chat_id)

            t1 = datetime.time(19,5,00,0000,tzinfo=eastern)
            weekly_job = context.job_queue.run_daily(weekly_top_mention,t1,days=(5),context=chat_id)

            t2 = datetime.time(0,10,00,0000)
            monthly_job = context.job_queue.run_daily(monthly_top_mention,t2,days=(0,1,2,3,4,5,6),context=chat_id)
            context.chat_data['job'] = [new_job,daily_job,weekly_job,monthly_job]
            #context.chat_data['job'] = [new_job,daily_job]
            update.message.reply_text('News alerts successfully set!')

        except:
            #update.message.reply_text("An error has occured setting up the news alerts")
            pass
        return SUBSCRIBE


def received_information(update, context):
    text = update.message.text
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    if first_name is None:
        first_name = 'N/A'
    last_name = update.message.chat.last_name
    if last_name is None:
        last_name = 'N/A'
    # Convert userTime into string
    userTime= update.message.date
    # userTime= datetime.datetime.fromtimestamp(userTime)
    userTime= userTime.strftime('%Y-%m-%d %H:%M:%S')
    content = update.message.text
    if content is None:
        content = 'N/A'

    user_input = text.upper().split(',')
    invalid_list=[] #To record all the invalid tickers
    repeat_list=[]
    # record abnormality
    for each in user_input:
        each = each.replace(' ','')
        if each not in allTicker_list:
            invalid_list.append(each)
        elif each in valid_list:
            repeat_list.append(each)

    if len(user_input)+len(valid_list)>3:
        update.message.reply_text('Please enter up to'+str(3-len(valid_list))+'valid stock ticker(s) Seperate with ,')
        return ENTER_TICKER
    elif len(invalid_list)!=0:
        update.message.reply_text(
            'Invalid ticker:{} Please enter up valid stock ticker(s) Seperate with ,'.format(listToString(invalid_list))
        )
        invalid_list=[]
        return ENTER_TICKER
    elif len(repeat_list)!=0:
        update.message.reply_text(
            'You have already subscribed to {}. Please enter new ticker(s)'.format(listToString(repeat_list))
        )
        return ENTER_TICKER
    else:
        for each in user_input:
            valid_list.append(each)
            context.user_data[each]="ticker"
        num = 3-len(valid_list)
        if num<0:
            num=0
        update.message.reply_text(
            'Alright. You have have subscribed to the news alert of:\n\N{pushpin} '+"\n\N{pushpin} ".join(valid_list)+
            '\nYou can subscribe to additional '+str(num)+' ticker(s)'
            "\nNews Alerts will arrive soon. Enjoy your day.",
            reply_markup=markup
        )


        try:
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()

            new_job = context.job_queue.run_repeating(make_alert,30,context=chat_id)

            #UTC 19:00
            eastern = timezone('US/Eastern')
            t = datetime.time(14,30,00,0000, tzinfo=eastern)
            daily_job = context.job_queue.run_daily(daily_top_mention,t,days=(0,1,2,3,4,5,6),context=chat_id)

            t1 = datetime.time(19,5,00,0000,tzinfo=eastern)
            weekly_job = context.job_queue.run_daily(weekly_top_mention,t1,days=(5),context=chat_id)

            t2 = datetime.time(0,10,00,0000)
            monthly_job = context.job_queue.run_daily(monthly_top_mention,t2,days=(0,1,2,3,4,5,6),context=chat_id)
            context.chat_data['job'] = [new_job,daily_job,weekly_job,monthly_job]
            #context.chat_data['job'] = [new_job,daily_job]
            update.message.reply_text('News alerts successfully set!')

        except:
            #update.message.reply_text("An error has occured setting up the news alerts")
            pass
        return SUBSCRIBE

def to_be_edited(update,context):

    user_data=context.user_data
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    if first_name is None:
        first_name = 'N/A'
    last_name = update.message.chat.last_name
    if last_name is None:
        last_name = 'N/A'
    # Convert userTime into string
    userTime= update.message.date
    # userTime= datetime.datetime.fromtimestamp(userTime)
    userTime= userTime.strftime('%Y-%m-%d %H:%M:%S')
    content = update.message.text
    if content is None:
        content = 'N/A'

    if len(valid_list)!=0:
        reply_keyboard=[]
        for ticker in valid_list:
            reply_keyboard.append([ticker])
        # should be a list of list of tickers that user entered
        reply_keyboard.append(["I'm good"])
        markup1 = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        try:
            update.message.reply_text("Which stock would you like to edit?",
                                    reply_markup = markup1)
            return EDIT
        except:

            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()

            new_job = context.job_queue.run_repeating(make_alert,30,context=chat_id)

            #UTC 19:00
            eastern = timezone('US/Eastern')
            t = datetime.time(14,30,00,0000, tzinfo=eastern)
            daily_job = context.job_queue.run_daily(daily_top_mention,t,days=(0,1,2,3,4,5,6),context=chat_id)

            t1 = datetime.time(19,5,00,0000,tzinfo=eastern)
            weekly_job = context.job_queue.run_daily(weekly_top_mention,t1,days=(5),context=chat_id)

            t2 = datetime.time(0,10,00,0000)
            monthly_job = context.job_queue.run_daily(monthly_top_mention,t2,days=(0,1,2,3,4,5,6),context=chat_id)
            context.chat_data['job'] = [new_job,daily_job,weekly_job,monthly_job]
            #context.chat_data['job'] = [new_job,daily_job]
            update.message.reply_text('News alerts successfully set!')
            return SUBSCRIBE


    else:
        reply_keyboard = [['Subscribe','My Subscription'],['Feedback','Join Waitlist']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("You have 0 subscriptions to edit. Please subscribe first.",reply_markup=markup)
        return SUBSCRIBE

def check_current_setting(update,context):
    text = update.message.text
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    if first_name is None:
        first_name = 'N/A'
    last_name = update.message.chat.last_name
    if last_name is None:
        last_name = 'N/A'
    # Convert userTime into string
    userTime= update.message.date
    # userTime= datetime.datetime.fromtimestamp(userTime)
    userTime= userTime.strftime('%Y-%m-%d %H:%M:%S')
    content = update.message.text
    if content is None:
        content = 'N/A'

    if len(valid_list)>0:
        reply_keyboard=[]
        for ticker in valid_list:
            reply_keyboard.append([InlineKeyboardButton(ticker,callback_data=ticker)])
        # should be a list of list of tickers that user entered
        markup1 = InlineKeyboardMarkup(reply_keyboard)
        update.message.reply_text("Here's your current subscriptions:\n\N{pencil} "+"\n\N{pencil} ".join(valid_list),reply_markup=markup)
        try:
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()

            new_job = context.job_queue.run_repeating(make_alert,30,context=chat_id)

            #UTC 19:00
            eastern = timezone('US/Eastern')
            t = datetime.time(14,30,00,0000, tzinfo=eastern)
            daily_job = context.job_queue.run_daily(daily_top_mention,t,days=(0,1,2,3,4,5,6),context=chat_id)

            t1 = datetime.time(19,5,00,0000,tzinfo=eastern)
            weekly_job = context.job_queue.run_daily(weekly_top_mention,t1,days=(5),context=chat_id)

            t2 = datetime.time(0,10,00,0000)
            monthly_job = context.job_queue.run_daily(monthly_top_mention,t2,days=(0,1,2,3,4,5,6),context=chat_id)
            context.chat_data['job'] = [new_job,daily_job,weekly_job,monthly_job]
            #context.chat_data['job'] = [new_job,daily_job]
            update.message.reply_text('News alerts successfully set!')

        except:
            #update.message.reply_text("An error has occured setting up the news alerts")
            pass
        return SUBSCRIBE
    else:
        update.message.reply_text("You haven't subscribed to any tickers yet. \nPlease add tickers to subscribe.",reply_markup=markup)
        return SUBSCRIBE
def change_to(update,context):
    text = update.message.text.upper() # one of the tickers the user entered
    try:
        valid_list.remove(text)
    except:
        pass
    try:
        del context.user_data[text]

    except:
        pass
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    if first_name is None:
        first_name = 'N/A'
    last_name = update.message.chat.last_name
    if last_name is None:
        last_name = 'N/A'
    # Convert userTime into string
    userTime= update.message.date
    # userTime= datetime.datetime.fromtimestamp(userTime)
    userTime= userTime.strftime('%Y-%m-%d %H:%M:%S')
    content = update.message.text
    if content is None:
        content = 'N/A'

    if text == "I'M GOOD":
        update.message.reply_text("Here's your current subscriptions:\n\N{pencil} "+"\n\N{pencil} ".join(valid_list),reply_markup=markup)
        try:
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()

            new_job = context.job_queue.run_repeating(make_alert,30,context=chat_id)

            #UTC 19:00
            eastern = timezone('US/Eastern')
            t = datetime.time(14,30,00,0000, tzinfo=eastern)
            daily_job = context.job_queue.run_daily(daily_top_mention,t,days=(0,1,2,3,4,5,6),context=chat_id)

            t1 = datetime.time(19,5,00,0000,tzinfo=eastern)
            weekly_job = context.job_queue.run_daily(weekly_top_mention,t1,days=(5),context=chat_id)

            t2 = datetime.time(0,10,00,0000)
            monthly_job = context.job_queue.run_daily(monthly_top_mention,t2,days=(0,1,2,3,4,5,6),context=chat_id)
            context.chat_data['job'] = [new_job,daily_job,weekly_job,monthly_job]
            #context.chat_data['job'] = [new_job,daily_job]
            update.message.reply_text('News alerts successfully set!')

        except:

            pass
        return SUBSCRIBE
    else:
        try:
            update.message.reply_text("Sure. Enter a new stock ticker to replace {}".format(text))
            return ENTER_TICKER
        except:
            if 'job' in context.chat_data:
                old_job = context.chat_data['job']
                old_job.schedule_removal()

            new_job = context.job_queue.run_repeating(make_alert,30,context=chat_id)

            #UTC 19:00
            eastern = timezone('US/Eastern')
            t = datetime.time(14,30,00,0000, tzinfo=eastern)
            daily_job = context.job_queue.run_daily(daily_top_mention,t,days=(0,1,2,3,4,5,6),context=chat_id)

            t1 = datetime.time(19,5,00,0000,tzinfo=eastern)
            weekly_job = context.job_queue.run_daily(weekly_top_mention,t1,days=(5),context=chat_id)

            t2 = datetime.time(0,10,00,0000)
            monthly_job = context.job_queue.run_daily(monthly_top_mention,t2,days=(0,1,2,3,4,5,6),context=chat_id)
            context.chat_data['job'] = [new_job,daily_job,weekly_job,monthly_job]
            #context.chat_data['job'] = [new_job,daily_job]
            update.message.reply_text('News alerts successfully set!')
            return SUBSCRIBE

def listToString(s):

    # initialize an empty string
    str1 = " "

    # return string
    return (str1.join(s))


def make_alert(context):
    job = context.job
    # read news json file
    with open({Path to the scraped news file}) as f:
        latest_news = json.load(f)
    for ticker in valid_list:
        for news in latest_news['data']:
            if ticker in news['tickers'] and news['news_url'] not in valid_news:
                # update.callback_query.answer()
                # context.bot.send_message(
                #     job.context, text="<b>"+ticker+"</b>"+"\n"+news['title']+":\n"+news['text']+'\n'+news['news_url'],parse_mode=telegram.ParseMode.HTML)
                try:
                    context.bot.send_message(
                        job.context, text="<b>"+listToString(news['tickers'])+"</b>"+"\n"+"[Sentiment] "+news['sentiment']+"\n"+"[Title] "+news['title']+":\n"+"[Summary] "+news['text']+'\n'+news['news_url'],parse_mode=telegram.ParseMode.HTML)
                except:
                    context.bot.send_message(
                        job.context, text="<b>"+listToString(news['tickers'])+"</b>"+"\n"+"[Sentiment] "+news['sentiment']+"\n"+"[Title] "+news['title']+":\n"+news['news_url'],parse_mode=telegram.ParseMode.HTML)
                valid_news.append(news['news_url'])

def daily_top_mention(context):
    job=context.job
    with open({path to the scraped news file}) as f:
        top_mention=json.load(f)
    msg="Top mentioned tickers today\n"
    for each in top_mention['data']['all']:
        num=top_mention['data']['all'].index(each)+1
        msg=msg+str(num)+". "+each['ticker']+'\t'+each['name']+"\t"+"total mention: "+str(each['total_mentions'])+"\n"
    try:
        context.bot.send_message(
            job.context,text=msg
        )
    except:
        pass
def weekly_top_mention(context):
    job=context.job
    with open({path to the scraped news file}) as f:
        top_mention=json.load(f)
    msg="Top mentioned tickers this week\n"
    for each in top_mention['data']['all']:
        num=top_mention['data']['all'].index(each)+1
        msg=msg+str(num)+". "+each['ticker']+'\t'+each['name']+"\t"+"total mention: "+str(each['total_mentions'])+"\n"
    try:
        context.bot.send_message(
            job.context,text=msg
        )
    except:
        pass

def monthly_top_mention(context):
    job=context.job
    with open({path to the scraped news file}) as f:
        top_mention=json.load(f)
    msg="Top mentioned tickers in the last month\n"
    for each in top_mention['data']['all']:
        num=top_mention['data']['all'].index(each)+1
        msg=msg+str(num)+". "+each['ticker']+'\t'+each['name']+"\t"+"total mention: "+str(each['total_mentions'])+"\n"
    try:
        context.bot.send_message(
            job.context,text=msg
        )
    except:
        pass

def join_queue(update,context):
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    if first_name is None:
        first_name = "N/A"
    last_name = update.message.chat.last_name
    if last_name is None:
        last_name = "N/A"
    # Convert userTime into string
    userTime= update.message.date

    update.message.reply_text("Thanks for your interest. You are on the waitlist.",reply_markup=markup)

    if 'job' in context.chat_data:
        old_job = context.chat_data['job']
        old_job.schedule_removal()

    new_job = context.job_queue.run_repeating(make_alert,30,context=chat_id)

    #UTC 19:00
    eastern = timezone('US/Eastern')
    t = datetime.time(14,30,00,0000, tzinfo=eastern)
    daily_job = context.job_queue.run_daily(daily_top_mention,t,days=(0,1,2,3,4,5,6),context=chat_id)

    t1 = datetime.time(19,5,00,0000,tzinfo=eastern)
    weekly_job = context.job_queue.run_daily(weekly_top_mention,t1,days=(5),context=chat_id)

    t2 = datetime.time(0,10,00,0000)
    monthly_job = context.job_queue.run_daily(monthly_top_mention,t2,days=(0,1,2,3,4,5,6),context=chat_id)
    context.chat_data['job'] = [new_job,daily_job,weekly_job,monthly_job]
    #context.chat_data['job'] = [new_job,daily_job]
    update.message.reply_text('News alerts successfully set!')

    #except:
        #update.message.reply_text("An error has occured setting up the news alerts")
        #pass
    return SUBSCRIBE

def unset(update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        update.message.reply_text('You have no active subscription')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    if first_name is None:
        first_name = 'N/A'
    last_name = update.message.chat.last_name
    if last_name is None:
        last_name = 'N/A'
    # Convert userTime into string
    userTime= update.message.date
    # userTime= datetime.datetime.fromtimestamp(userTime)
    userTime= userTime.strftime('%Y-%m-%d %H:%M:%S')
    content = update.message.text
    if content is None:
        content = 'N/A'

    update.message.reply_text('Alert successfully unset!')


def greet_feedback(update,context):
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    if first_name is None:
        first_name ="N/A"
    last_name = update.message.chat.last_name
    if last_name is None:
        last_name ="N/A"
    # Convert userTime into string
    userTime= update.message.date
    # userTime= datetime.datetime.fromtimestamp(userTime)
    userTime= userTime.strftime('%Y-%m-%d %H:%M:%S')

    update.message.reply_text("Please write down your feedback. We appreciate your time and opinions")
    return FEEDBACK

def feedback(update, context):
    chatId = update.message.chat.id
    userTime= update.message.date
    firstName = update.message.chat.first_name
    if firstName is None:
        firstName = "N/A"
    lastName = update.message.chat.last_name
    if lastName is None:
        lastName = "N/A"
    chatContent = update.message.text #user feedback
    if chatContent is None:
        chatContent = "N/A"
    #timestamp = datetime.datetime.fromtimestamp(userTime) timestamp.strftime('%Y-%m-%d %H:%M:%S')

    update.message.reply_text('Thanks for your feedback',reply_markup = markup)

    try:
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()

        new_job = context.job_queue.run_repeating(make_alert,30,context=chat_id)

        #UTC 19:00
        eastern = timezone('US/Eastern')
        t = datetime.time(19,00,00,0000, tzinfo=eastern)
        daily_job = context.job_queue.run_daily(daily_top_mention,t,days=(0,1,2,3,4,5,6),context=chat_id)

        t1 = datetime.time(19,5,00,0000,tzinfo=eastern)
        weekly_job = context.job_queue.run_daily(weekly_top_mention,t1,days=(5),context=chat_id)

        t2 = datetime.time(19,10,00,0000,tzinfo=eastern)
        monthly_job = context.job_queue.run_daily(monthly_top_mention,t2,days=(0,1,2,3,4,5,6),context=chat_id)
        context.chat_data['job'] = [new_job,daily_job,weekly_job,monthly_job]
        #context.chat_data['job'] = [new_job,daily_job]
        update.message.reply_text('News alerts successfully set!')

    except:
        #update.message.reply_text("An error has occured setting up the news alerts")
        pass
    return SUBSCRIBE

def help(update, context):
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    if first_name is None:
        first_name = "N/A"
    last_name = update.message.chat.last_name
    if last_name is None:
        last_name = "N/A"
    # Convert userTime into string
    userTime= update.message.date
    # userTime= datetime.datetime.fromtimestamp(userTime)
    userTime= userTime.strftime('%Y-%m-%d %H:%M:%S')
    content = update.message.text
    if content is None:
        content="N/A"

    if valid_list:
        update.message.reply_text("You have subscribed to :"
                            "{}"
                            "\n If you cannot receive news alerts, press /receive"
                            "\n To stop receiving news alerts, click /stop"
                            "\n If you cannot receive response after pressing /start ,type something to wake me up"
                            "\n If you wish to return to the start menu, type something to let me know".format(listToString(valid_list)))
    else:
        update.message.reply_text("You haven't subscribed to any tickers yet"
                            "\n Press /start to subscribe" )

def main():
    #pp = PicklePersistence(filename='conversationbot')
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(telegram_token, use_context=True)#, persistence=pp)

    # clear the record
    valid_list = []

    # Get the dispatcher to register handlers
    dp = updater.dispatcher




    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    # first level
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            SUBSCRIBE: [MessageHandler(Filters.regex('^Subscribe$'),
                                      subscribe),
                       MessageHandler(Filters.regex('^My Subscription$'),
                                      to_be_edited),
                        MessageHandler(Filters.regex('^Feedback$'),
                                      greet_feedback),
                        MessageHandler(Filters.regex('^Join Waitlist$'),
                                      join_queue),
                        MessageHandler(Filters.regex('^Check$'),
                                      check_current_setting),
                       ],

            ENTER_TICKER: [
                MessageHandler(Filters.text & ~(Filters.regex('^Done$')),
                               received_information),
                MessageHandler(Filters.regex('^/start$'),start),
            ],


            EDIT: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')),
                               change_to),
                MessageHandler(Filters.regex('^/start$'),start)],
            BACK_TO_STEP_1: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')),
                               start)],

            FEEDBACK: [
                MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')),
                               feedback),
                MessageHandler(Filters.regex('^/start$'),start)],

        },

        fallbacks=[MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^/start')),start)],
        #persistent=True, name='myconversation',
    )

    dp.add_handler(conv_handler)

    dp.add_handler(CommandHandler("stop", unset, pass_chat_data=True))
    dp.add_handler(CommandHandler("help", help,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
