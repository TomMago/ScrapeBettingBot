#!/usr/bin/env python3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler
import os
import json
import pandas as pd
import numpy as np
import telegram
from datetime import datetime, timedelta


def scrape_odds(bot, job):
    chatid, date = job.context
    bot.send_message(chat_id=chatid,
                     text='Start scraping...')
    os.system('rm odds_test.json')
    #os.system('scrapy crawl odds -o odds_test.json -a date='+date)
    os.system('scrapy crawl odds -o odds_test.json -a date='+date)
    bot.send_message(chat_id=chatid,
                     text='Finished scraping!')


def gen_odd_dataset(bot, job):
    chatid, date = job.context
    bot.send_message(chat_id=chatid,
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
                                          'Std_ps_Home': np.std(1/np.array(odds['odd1']).astype(np.float)),
                                          'Max_Bookie_Home': odds['bookie'][np.argmax(np.array(odds['odd1']).astype(np.float))],
                                          'Mean_Odd_Draw': np.mean(np.array(odds['oddX']).astype(np.float)),
                                          'Max_Odd_Draw': np.max(np.array(odds['oddX']).astype(np.float)),
                                          'Std_ps_Draw': np.std(1/np.array(odds['oddX']).astype(np.float)),
                                          'Max_Bookie_Draw': odds['bookie'][np.argmax(np.array(odds['oddX']).astype(np.float))],
                                          'Mean_Odd_Away': np.mean(np.array(odds['odd2']).astype(np.float)),
                                          'Max_Odd_Away': np.max(np.array(odds['odd2']).astype(np.float)),
                                          'Std_ps_Away': np.std(1/np.array(odds['odd2']).astype(np.float)),
                                          'Max_Bookie_Away': odds['bookie'][np.argmax(np.array(odds['odd2']).astype(np.float))],
                                          'Number_Odds': row['Number_Odds']},
                                         ignore_index=True)
    bot.send_message(chat_id=chatid,
                     text='Build dataset with '+str(len(datasetdf))+' bets!')
    return datasetdf

def bet(means, maxes, Theta):
    eps = 0.0001
    phi = maxes - 1/(np.maximum(1/means - Theta, eps))
    return np.heaviside(phi, 1)

def find_value_bets(bot, job, df, bet_on, Theta):
    bets = bet(df['Mean_Odd_'+bet_on].values, df['Max_Odd_'+bet_on].values, Theta)
    bet_info = df.loc[bets == 1]
    return bet_info

def current_value_bets(bot, job):
    chatid, date = job.context
    bot.send_message(chat_id=chatid, text="Searching bets...")
    scrape_odds(bot, job)
    THETA_HOME = 0.055
    THETA_DRAW = 0.057
    THETA_AWAY = 0.037
    df = gen_odd_dataset(bot, job)
    for result_tag in ["Home", "Draw", "Away"]:
        bot.send_message(chat_id=chatid, text="<b>" + result_tag + " bets: </b>", parse_mode=telegram.ParseMode.HTML)
        for index, bet in find_value_bets(bot, job, df, result_tag, THETA_HOME).iterrows():
            if bet['Number_Odds'] > 7:
                #bot.send_message(chat_id=chatid,
                #                 text="Profitable Bet!\n"+bet['Home']+" vs. "+bet['Away']+"\n\nBet on: " + bet['Home']+ "\nBookmaker:" + bet['Max_Bookie_Home'] + "\nmean odd: " + str(bet['Mean_Odd_Home']) + "\nmax odd:" + str(bet['Max_Odd_Home']))
                kelly = 1/bet['Mean_Odd_'+result_tag] + (1/bet['Mean_Odd_'+result_tag] - 1) / (bet['Max_Odd_'+result_tag] - 1)
                edge = 1/bet['Mean_Odd_'+result_tag] - 1/bet['Max_Odd_'+result_tag]
                if result_tag == "Draw":
                    to_bet = "Draw"
                else:
                    to_bet = bet[result_tag]
                bot.send_message(chat_id=chatid,
                                 text="Profitable Bet!                <b>" + str(int(bet['Number_Odds'])) + "</b> Odds\n<i>"+bet['Home']
                                 + " vs. " + bet['Away'] + "</i>\n\nBet on:                  <b>"
                                 + to_bet + "</b>\nBookmaker:         <b>"
                                 + bet['Max_Bookie_'+result_tag] + "</b>\nmean odd:            <b>"
                                 + "{:.2f}".format(bet['Mean_Odd_'+result_tag]) + "</b><i>  ~  {:.3f}".format(1/bet['Mean_Odd_'+result_tag]) + "</i>\nmax odd:              <b>"
                                 + "{:.2f}".format(bet['Max_Odd_'+result_tag]) + "</b><i>  ~  {:.3f}".format(1/bet['Max_Odd_'+result_tag]) + "</i>\nmean prob std:    <b>"
                                 + "{:.3f}".format(bet['Std_ps_'+result_tag]) + "</b>\nedge:                     <b>"
                                 + "{:.1f}".format(edge*100) + "%</b>\nKelly crit:               <b>"
                                 + "{:.1f}".format(kelly*100) + "%</b>\nBaker-McHale:     <b>"
                                 + "{:.1f}".format(kelly*edge**2/bet['Std_ps_'+result_tag]**2/(edge**2/bet['Std_ps_'+result_tag]**2 + 1)*100) + "%</b>\n0.4 fractional:       <b>"
                                 + "{:.1f}".format(0.4*kelly*edge**2/bet['Std_ps_'+result_tag]**2/(edge**2/bet['Std_ps_'+result_tag]**2 + 1)*100) + "%</b>",
                                 parse_mode=telegram.ParseMode.HTML)

#def start_bot(bot, update, job_queue):
#    bot.send_message(chat_id=update.message.chat_id,
#                      text='Starting...')
#    from datetime import timedelta
#    #job_queue.run_repeating(current_value_bets, , context=update.message.chat_id)
#    job_queue.run_once(current_value_bets, timedelta(0,3), context=update.message.chat_id)

def bets_today(bot, update, job_queue):
    bot.send_message(chat_id=update.message.chat_id,
                      text='Starting...')
    job_queue.run_once(current_value_bets, timedelta(0,3), context=(update.message.chat_id, "today"))

def bets_tomorrow(bot, update, job_queue):
    bot.send_message(chat_id=update.message.chat_id,
                      text='Starting...')
    from datetime import timedelta
    job_queue.run_once(current_value_bets, timedelta(0,3), context=(update.message.chat_id, "tomorrow"))

def bets_days(bot, update, job_queue, args):
    bot.send_message(chat_id=update.message.chat_id,
                      text='Starting...')
    from datetime import timedelta
    job_queue.run_once(current_value_bets, timedelta(0,3), context=(update.message.chat_id, args[0]+"-days"))

def ping(bot, update, job_queue):
    bot.send_message(chat_id=update.message.chat_id,
                      text='Ping: ' + str(datetime.now()))
    job_queue.stop()

def stop_bot(bot, update, job_queue):
    bot.send_message(chat_id=update.message.chat_id,
                      text='Stopped!')
    job_queue.stop()

def main():
    updater = Updater("xxx")
    dp = updater.dispatcher
    #dp.add_handler(MessageHandler(Filters.text, time,pass_job_queue=True))
    dp.add_handler(CommandHandler('today', bets_today, pass_job_queue=True))
    dp.add_handler(CommandHandler('tomorrow', bets_tomorrow, pass_job_queue=True))
    dp.add_handler(CommandHandler('days', bets_days, pass_job_queue=True, pass_args=True))
    dp.add_handler(CommandHandler('ping', ping, pass_job_queue=True))
    dp.add_handler(CommandHandler('stop', stop_bot, pass_job_queue=True))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
