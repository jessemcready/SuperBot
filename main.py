import discord
import asyncio
from lxml import html
import requests

client = discord.Client()

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

        page = requests.get('https://na.op.gg/champion/' + champion + '/statistics/' + role)
        tree = html.fromstring(page.content)
        bestBuild = extractBuild(tree)
        bestSkill = extractSkills(tree)
        bestKeystone = extractKeystone(tree)
        bestMasteries = extractMasteries(tree)
        bestRunes = extractRunes(tree)
        weakAgainst = extractWeakAgainst(tree)
        strongAgainst = extractStrongAgainst(tree)
        skillString = ''.join(bestSkill)
        await client.send_message(message.channel, 'https://na.op.gg/champion/' + champion + '/statistics/' + role + '\nTLDR: \n\nCore Build: \n' + bestBuild[0] + ' -> ' + bestBuild[1] + ' -> ' + bestBuild[2] +'\n\nSkills: \n' + skillString[0] + ' -> ' + skillString[1] + ' -> ' + skillString[2] + '\n\nKeystone And Masteries\n' + bestKeystone + '\t' + bestMasteries + '\n\nRunes\n' + bestRunes + '\n\nWeak Against: ' + weakAgainst + '\nStrong Against: ' + strongAgainst)
    if message.content.startswith('.help'):
        await client.send_message(message.channel, 'To get champion data, type !<champion name> <role>\n' + 'Or type .yt <search terms> to get a YouTube video')
    if message.content.startswith('.yt'):
        tempMessage = message.content[4:]
        tempMessage = tempMessage.replace(' ', '+')
        page = requests.get('https://www.youtube.com/results?search_query=' + tempMessage)
        tree = html.fromstring(page.content)
        videoLink = tree.xpath('//*[@id="results"]//ol//li[2]//ol//li//div//div//div[2]//h3//a/@href')
        link = ''.join(videoLink)
        link = link[1:]
        youTubeLink = link.split('/')
        await client.send_message(message.channel, 'https://www.youtube.com/' + youTubeLink[0])

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

client.run('<Your token here>')
