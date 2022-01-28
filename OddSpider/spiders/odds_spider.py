#!/usr/bin/env python3

import scrapy
from scrapy_splash import SplashRequest
from datetime import datetime, timedelta


class OddsSpider(scrapy.Spider):
    name = "odds"
    baseurl = "https://www.betexplorer.com"

    def __init__(self, date='today', **kwargs):
        if date == 'today':
            self.urls = ['https://www.betexplorer.com/next/soccer/']
        elif date == 'tomorrow':
            datestring = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
            year = datestring[:4]
            month = datestring[5:7]
            day = datestring[8:10]
            self.urls = ['https://www.betexplorer.com/next/soccer/?year=' + year + '&month=' + month + '&day=' + day]
        elif "days" in date:
            days = date[:-5]
            datestring = (datetime.today() + timedelta(days=int(days))).strftime('%Y-%m-%d')
            year = datestring[:4]
            month = datestring[5:7]
            day = datestring[8:10]
            self.urls = ['https://www.betexplorer.com/next/soccer/?year=' + year + '&month=' + month + '&day=' + day]
        super().__init__(**kwargs)

    def start_requests(self):
        for url in self.urls:
            #yield #scrapy.Request(url=url, callback=self.parse)
            yield SplashRequest(url, self.parse, args={'wait':0.5})


    def parse(self, response):
        #self.log(response.css('.table-main tr td').getall())
        game_links = []

        for a_elem in response.css('.table-main .table-main__tt'):
            game_links.append(a_elem.css('a::attr(href)').get())

        #yield {'links': game_links}

        for link in game_links:
            game_page = response.urljoin(self.baseurl + link)
            yield SplashRequest(game_page, self.parse_game, args={'wait':0.5})


        #filename = f'odds.html'
        #with open(filename, 'wb') as f:
        #    f.write(response.body)
        #self.log(f'Saved file {filename}')

    def parse_game(self, response):
        bookies = []
        for bookie in response.css('#odds-content tbody tr'):
            #yield {'bookie': bookie.css('a.in-bookmaker-logo-link::text').get(),
            #       'odd1': bookie.css('td.table-main__detail-odds')[0].css('span.table-main__detail-odds--hasarchive::text').get(),
            #       'oddX': bookie.css('td.table-main__detail-odds')[1].css('span.table-main__detail-odds--hasarchive::text').get(),
            #       'odd2': bookie.css('td.table-main__detail-odds')[2].css('span.table-main__detail-odds--hasarchive::text').get()}
            bookies.append({'bookie': bookie.css('a.in-bookmaker-logo-link::text').get(),
                            #'odd1': bookie.css('td.table-main__detail-odds')[0].css('span.table-main__detail-odds--hasarchive::text').get(),
                            #'oddX': bookie.css('td.table-main__detail-odds')[1].css('span.table-main__detail-odds--hasarchive::text').get(),
                            #'odd2': bookie.css('td.table-main__detail-odds')[2].css('span.table-main__detail-odds--hasarchive::text').get()})
                            'odd1': bookie.css('td.table-main__detail-odds:not(.inactive)')[0].css('::attr(data-odd)').get(),
                            'oddX': bookie.css('td.table-main__detail-odds:not(.inactive)')[1].css('::attr(data-odd)').get(),
                            'odd2': bookie.css('td.table-main__detail-odds:not(.inactive)')[2].css('::attr(data-odd)').get()})
        yield {'Home': response.css('.list-details__item__title')[0].css('a::text').get(),
               'Away': response.css('.list-details__item__title')[1].css('a::text').get(),
               'Number_Odds': len(bookies),
               'Odds': [bookie for bookie in bookies]}
