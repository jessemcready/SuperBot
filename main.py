import discord
from riotwatcher import RiotWatcher
import asyncio
from lxml import html
import requests
from requests import HTTPError
import json
import config
import string

client = discord.Client()
watcher = RiotWatcher(config.riotApiKey)
my_region = 'na1' # change based on whatever server you're on

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('-----')

@client.event
async def on_message(message):
    if message.content.startswith('!'):
        # extract champion name
        champion, role = message.content.split(" ")
        champion = champion[1:]
        if role == "mid":
            role = "middle"
        if role == "jg":
            role = "jungle"

        # get the page
        page = requests.get('https://na.op.gg/champion/' + champion + '/statistics/' + role)
        # build an xml tree
        tree = html.fromstring(page.content)
        # parse the tree for builds, skills, keystones, etc
        bestBuild = extractBuild(tree)
        bestSkill = extractSkills(tree)
        bestRunes = extractRunes(tree)
        skillString = ''.join(bestSkill)
        # send a message from the bot to discord
        await client.send_message(message.channel, 'https://na.op.gg/champion/' + champion + '/statistics/' + role + '\nTLDR: \n\nCore Build: \n' + bestBuild +'\n\nSkills: \n' + skillString + '\n\nRunes\n' + bestRunes)
    if message.content.startswith('.help'):
        await client.send_message(message.channel, 'To get summoner data, type .rank <summoner1>,<summoner2>...To get champion data, type !<champion name> <role>\n' + 'Or type .yt <search terms> to get a YouTube video')
    if message.content.startswith('.yt'):
        # gets rid of the ".yt " when parsing the message
        tempMessage = message.content[4:]
        # youtube uses '+' instead of ' ' so just sub out
        tempMessage = tempMessage.replace(' ', '+')
        page = requests.get('https://www.youtube.com/results?search_query=' + tempMessage)
        tree = html.fromstring(page.content)
        videoLink = tree.xpath('//*[@id="results"]//ol//li[2]//ol//li//div//div//div[2]//h3//a/@href')
        link = ''.join(videoLink)
        link = link[1:]
        # sometimes you will have multiple number sets separated by '/' and you want the first one
        youTubeLink = link.split('/')
        await client.send_message(message.channel, 'https://www.youtube.com/' + youTubeLink[0])
    if message.content.startswith('.rank'):
        summonerMessage = message.content[6:]
        # check to see if any summoners were asked for
        if len(summonerMessage) == 0:
            await client.send_message(message.channel, 'Oops, seems like you need to add some summoner names!')
        # put a cap on the number to enforce rate limiting
        if summonerMessage.count(',') == 9:
            await client.send_message(message.channel, 'We only allow 10 summoner names at a time!')
        summoners = summonerMessage.split(', ')
        summonerString = ' '
        summonerData = getSummonerData(summoners)
        for i in range(len(summonerData)):
            summonerString += summonerData[i] + '\n'
        await client.send_message(message.channel, summonerString)

# used for checking errors when accessing RIOT api
# 429 for too many requests
# 400 for summoner not found
try:
    response = watcher.summoner.by_name(my_region, 'this_is_probably_not_anyones_summoner_name')
except HTTPError as err:
    if err.response.status_code == 429:
        print('We should retry in {} seconds.'.format(e.headers['Retry-After']))
        print('this retry-after is handled by default by the RiotWatcher library')
        print('future requests wait until the retry-after time passes')
    elif err.response.status_code == 404:
        print('Summoner with that ridiculous name not found.')
    else:
        raise

def extractBuild(tree):
    build = ''.join(tree.xpath('/html/body/div[1]/div[3]/div/div[2]/div[2]/div[1]/div/div[1]/table[2]/tbody/tr[3]/td[1]/ul//@title')).strip()
    build = build.split("<b style=", 3)
    firstItem = build[1][17:]
    firstItem = firstItem.split('<')
    firstItem = ''.join(firstItem[0])
    secondItem = build[2][17:]
    secondItem = secondItem.split('<')
    secondItem = ''.join(secondItem[0])
    thirdItem = build[3][17:]
    thirdItem = thirdItem.split('<')
    thirdItem = ''.join(thirdItem[0])
    finalBuild = firstItem + '->' + secondItem + '->' + thirdItem
    return finalBuild

def extractSkills(tree):
    skillOrder = ''
    for i in range(0, 15):
        skillOrder += ' '.join(tree.xpath('/html/body/div[1]/div[3]/div/div[2]/div[2]/div[1]/div/div[1]/table[1]/tbody[2]/tr/td[1]/table/tbody/tr[2]/td[' + str(i) + ']/text()')).strip()
    return skillOrder

def extractRunes(tree):
    keystone = ''.join(tree.xpath('/html/body/div[1]/div[3]/div/div[2]/div[2]/div[1]/div/div[1]/div/table/tbody[2]/tr[1]/td[1]/div/div[1]/div[@class="perk-page__item perk-page__item--keystone perk-page__item--active"]/div/img//@alt'))
    subRunes1 = tree.xpath('/html/body/div[1]/div[3]/div/div[2]/div[2]/div[1]/div/div[1]/div/table/tbody[2]/tr[1]/td[1]/div/div[1]/div[@class="perk-page__item  perk-page__item--active"]//@alt')
    subRunes2 = tree.xpath('/html/body/div[1]/div[3]/div/div[2]/div[2]/div[1]/div/div[1]/div/table/tbody[2]/tr[1]/td[1]/div/div[2]/div[@class="perk-page__item perk-page__item--active"]/div/img//@alt')
    runes = keystone + '\n' + subRunes1[0] + '->' + subRunes1[1] + '->' + subRunes1[2] + '\n' + subRunes2[0] + '->' + subRunes2[1]
    return runes

def getSummonerData(summonerNames):
    summoner_stats = []
    for summoner in summonerNames:
        summonerId = getSummonerId(summoner)
        summoner_stats_json = watcher.league.positions_by_summoner(my_region, summonerId)
        for leagues in summoner_stats_json:
            if leagues["queueType"] == "RANKED_SOLO_5x5":
                position = leagues['tier'] + ' ' + leagues['rank'] + ' ' + str(leagues['leaguePoints'])
                totalData = summoner + ' ' + position
                summoner_stats.append(totalData)
    return summoner_stats

def getSummonerId(summonerName):
    summonerJSON = watcher.summoner.by_name(my_region, summonerName)
    summonerId = summonerJSON['id']
    return summonerId

client.run(config.discordToken)
