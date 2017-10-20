import discord
from riotwatcher import RiotWatcher
import asyncio
from lxml import html
import requests
from requests import HTTPError
import json

client = discord.Client()
watcher = RiotWatcher('<riot game api>')
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
        bestKeystone = extractKeystone(tree)
        bestMasteries = extractMasteries(tree)
        bestRunes = extractRunes(tree)
        weakAgainst = extractWeakAgainst(tree)
        strongAgainst = extractStrongAgainst(tree)
        skillString = ''.join(bestSkill)
        # send a message from the bot to discord
        await client.send_message(message.channel, 'https://na.op.gg/champion/' + champion + '/statistics/' + role + '\nTLDR: \n\nCore Build: \n' + bestBuild[0] + ' -> ' + bestBuild[1] + ' -> ' + bestBuild[2] +'\n\nSkills: \n' + skillString[0] + ' -> ' + skillString[1] + ' -> ' + skillString[2] + '\n\nKeystone And Masteries\n' + bestKeystone + '\t' + bestMasteries + '\n\nRunes\n' + bestRunes + '\n\nWeak Against: ' + weakAgainst + '\nStrong Against: ' + strongAgainst)
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
        summonerData = getSummonerData(summoners)
        await client.send_message(message.channel, summonerData)

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
    build = tree.xpath('//tbody[@class="Content"]//tr[6]//td[@class="Cell ListCell"]//div[@class="Item"]//img//@alt')
    return build

def extractSkills(tree):
    skillOrder =  tree.xpath('//span[@class="ExtraString"]/text()')
    return skillOrder

def extractKeystone(tree):
    key = tree.xpath('//tbody[@class="Content"]//tr[14]//td[@class="Cell Single"]//div[@class="Name"]/text()')
    keystone = ''.join(key)
    return keystone

def extractMasteries(tree):
    ferocityMasteries = tree.xpath('/html/body/div[1]/div[3]/div[4]/div[4]/div[1]/div[1]/div/div/table/tbody/tr[16]/td[2]/div/div[1]/div[1]/strong/text()')
    cunningMasteries = tree.xpath('/html/body/div[1]/div[3]/div[4]/div[4]/div[1]/div[1]/div/div/table/tbody/tr[16]/td[2]/div/div[2]/div[1]/strong/text()')
    resolveMasteries = tree.xpath('/html/body/div[1]/div[3]/div[4]/div[4]/div[1]/div[1]/div/div/table/tbody/tr[16]/td[2]/div/div[3]/div[1]/strong/text()')

    ferMast = ''.join(ferocityMasteries)
    cunMast = ''.join(cunningMasteries)
    resMast = ''.join(resolveMasteries)

    masteries = ferMast + '/' + cunMast + '/' + resMast

    return masteries

def extractRunes(tree):
    testRunes = tree.xpath('/html/body/div[1]/div[3]/div[4]/div[4]/div[1]/div[1]/div/div/table/tbody/tr[18]/td[2]/div//*/text()')
    for i in range(0, len(testRunes)):
        if '\n' in testRunes[i] or '\t' in testRunes[i]:
            testRunes[i] = ''
        if 'x' in testRunes[i]:
            testRunes[i] = '\n' + testRunes[i]

    runes = ''.join(testRunes)
    return runes

def extractWeakAgainst(tree):
    weak = tree.xpath('//td[@class="ChampionName"]/text()')
    weakAgainst = ''.join(weak[0]) + ' ' + ''.join(weak[1]) + ' ' + ''.join(weak[2])
    return weakAgainst


def extractStrongAgainst(tree):
    strong = tree.xpath('//td[@class="ChampionName"]/text()')
    strongAgainst = ''.join(strong[3]) + ' ' + ''.join(strong[4]) + ' ' + ''.join(strong[5])
    return strongAgainst

def getSummonerData(summonerNames):
    summoner_stats = []
    for summoner in summonerNames:
        summonerId = getSummonerId(summoner)
        summoner_stats_json = watcher.league.positions_by_summoner(my_region, summonerId)
        position = summoner_stats_json[0]['tier'] + ' ' + summoner_stats_json[0]['rank']
        totalData = summoner + ' ' + position
        totalData.replace('[','')
        totalData.replace(']','')
        totalData.replace("'",'')
        summoner_stats.append(totalData)
    return summoner_stats

def getSummonerId(summonerName):
    summonerJSON = watcher.summoner.by_name(my_region, summonerName)
    summonerId = summonerJSON['id']
    return summonerId

client.run('<discord api key>')
