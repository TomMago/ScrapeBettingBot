#!/usr/bin/env python3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
import os
import json
import pandas as pd
import numpy as np

def scrape_odds(bot, job):
    bot.send_message(chat_id=job.context,
                     text='Start scraping...')
    os.system('rm odds_test.json')
    os.system('scrapy crawl odds -o odds_test.json')
    bot.send_message(chat_id=job.context,
                     text='Finished scraping!')


def gen_odd_dataset(bot, job):
    bot.send_message(chat_id=job.context,
                     text='Start generating dataset...')

    df = pd.read_json('odds_test.json')
    datasetdf = pd.DataFrame(columns=[])

    for index, row in df.iterrows():
        LD = row['Odds']
        if LD:
            odds = {k: [dic[k] for dic in LD] for k in LD[0]}
            datasetdf = datasetdf.append({'Home': row['Home'],
                                          'Away': row['Away'],
                                          'Mean_Odd_Home': np.mean(np.array(odds['odd1']).astype(np.float)),
                                          'Max_Odd_Home': np.max(np.array(odds['odd1']).astype(np.float)),
                                          'Max_Bookie_Home': odds['bookie'][np.argmax(np.array(odds['odd1']).astype(np.float))],
                                          'Mean_Odd_Draw': np.mean(np.array(odds['oddX']).astype(np.float)),
                                          'Max_Odd_Draw': np.max(np.array(odds['oddX']).astype(np.float)),
                                          'Max_Bookie_Draw': odds['bookie'][np.argmax(np.array(odds['oddX']).astype(np.float))],
                                          'Mean_Odd_Away': np.mean(np.array(odds['odd2']).astype(np.float)),
                                          'Max_Odd_Away': np.max(np.array(odds['odd2']).astype(np.float)),
                                          'Max_Bookie_Away': odds['bookie'][np.argmax(np.array(odds['odd2']).astype(np.float))]},
                                         ignore_index=True)
    bot.send_message(chat_id=job.context,
                     text='Build dataset with '+str(len(datasetdf))+' bets!')
    return datasetdf

def bet(means, maxes, Theta):
    phi = maxes - 1/(1/means - Theta)
    return np.heaviside(phi, 1)

def find_value_bets(bot, job, df, bet_on, Theta):
    bets = bet(df['Mean_Odd_'+bet_on].values, df['Max_Odd_'+bet_on].values, Theta)
    bet_info = df.loc[bets == 1]
    return bet_info

def current_value_bets(bot, job):
    bot.send_message(chat_id=job.context, text="Searching bets...")
    scrape_odds(bot, job)
    THETA_HOME = 0.034
    THETA_DRAW = 0.057
    THETA_AWAY = 0.037
    for index, bet in find_value_bets(bot, job, gen_odd_dataset(bot, job), "Home", THETA_HOME).iterrows():
        bot.send_message(chat_id=job.context,
                         text="Profitable Bet!\n"+bet['Home']+" vs. "+bet['Away']+"\n\nBet on: " + bet['Home']+ "\nBookmaker:" + bet['Max_Bookie_Home'] + "\nmean odd: " + str(bet['Mean_Odd_Home']) + "\nmax odd:" + str(bet['Max_Odd_Home']))

def start_bot(bot, update, job_queue):
    bot.send_message(chat_id=update.message.chat_id,
                      text='Starting...')
    from datetime import timedelta
    #job_queue.run_repeating(current_value_bets, , context=update.message.chat_id)
    job_queue.run_once(current_value_bets, timedelta(0,3), context=update.message.chat_id)

def stop_bot(bot, update, job_queue):
    bot.send_message(chat_id=update.message.chat_id,
                      text='Stopped!')
    job_queue.stop()

def main():
    updater = Updater("xxxx")
    dp = updater.dispatcher
    #dp.add_handler(MessageHandler(Filters.text, time,pass_job_queue=True))
    dp.add_handler(CommandHandler('start', start_bot, pass_job_queue=True))
    dp.add_handler(CommandHandler('stop', stop_bot, pass_job_queue=True))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
