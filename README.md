# ScrapeBettingBot

Scrape odds for upcoming sports matches and detect profitable bets

## installation

install scrapy:

``` shell
pip install Scrapy
```

install scrapy-splash

``` shell
pip install scrapy-splash
```

install docker and get the docker container for splash

``` shell
docker pull scrapinghub/splash
```

## Running the bot

First start splash

``` shell
docker run -p 8050:8050 scrapinghub/splash
```

Add address of splash to the settings of scrapy in settings.py of the spider:

``` python
SPLASH_URL = 'http://x.x.x.x:8050'
```

Add api key for the telegram bot in ScrapeBettingBot.py

``` python
updater = Updater("x:xxxx")
```

Start the telegram bot with

``` shell
python ScrapeBettingBot.py
```


