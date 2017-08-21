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
        skillString = ''.join(bestSkill)
        await client.send_message(message.channel, 'https://na.op.gg/champion/' + champion + '/statistics/' + role + '\nTLDR: \n\nCore Build: \n' + bestBuild[0] + ' -> ' + bestBuild[1] + ' -> ' + bestBuild[2] +'\n\nSkills: \n' + skillString[0] + ' -> ' + skillString[1] + ' -> ' + skillString[2] + '\n\nKeystone And Masteries\n' + bestKeystone + '\t' + bestMasteries + '\n\nRunes\n' + bestRunes[0] + '\n' + bestRunes[1] + '\n' + bestRunes[2] + '\n' + bestRunes[3] + '\n')
    if message.content.startswith('.help'):
        await client.send_message(message.channel, 'To get champion data, type !<champion name> <role>\n' + 'Or type .yt <search terms> to get a YouTube video')
    if message.content.startswith('.yt'):
        tempMessage = message.content[4:]
        tempMessage = tempMessage.replace(' ', '+')
        page = requests.get('https://www.youtube.com/results?search_query=' + tempMessage)
        tree = html.fromstring(page.content)
        videoLink = tree.xpath('//*[@id="results"]//ol//li[2]//ol//li//div//div//div[2]//h3//a/@href')
        link = ''.join(videoLink)
        await client.send_message(message.channel, 'https://www.youtube.com' + link)

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
    ferocityMasteries = tree.xpath('/html/body/div[1]/div[2]/div[2]/div[4]/div[4]/div[1]/div[1]/div/div/table/tbody/tr[16]/td[2]/div/div[1]/div[1]/strong/text()')
    cunningMasteries = tree.xpath('/html/body/div[1]/div[2]/div[2]/div[4]/div[4]/div[1]/div[1]/div/div/table/tbody/tr[16]/td[2]/div/div[2]/div[1]/strong/text()')
    resolveMasteries = tree.xpath('/html/body/div[1]/div[2]/div[2]/div[4]/div[4]/div[1]/div[1]/div/div/table/tbody/tr[16]/td[2]/div/div[3]/div[1]/strong/text()')

    ferMast = ''.join(ferocityMasteries)
    cunMast = ''.join(cunningMasteries)
    resMast = ''.join(resolveMasteries)

    masteries = ferMast + '/' + cunMast + '/' + resMast

    return masteries

def extractRunes(tree):
    marks = tree.xpath('//tbody[@class="Content"]//tr[18]//td[@class="Cell Single"]//div[@class="RuneItemList"]//div[1]//div/text()')
    glyphs = tree.xpath('//tbody[@class="Content"]//tr[18]//td[@class="Cell Single"]//div[@class="RuneItemList"]//div[2]//div/text()')
    seals = tree.xpath('//tbody[@class="Content"]//tr[18]//td[@class="Cell Single"]//div[@class="RuneItemList"]//div[3]//div/text()')
    quints = tree.xpath('//tbody[@class="Content"]//tr[18]//td[@class="Cell Single"]//div[@class="RuneItemList"]//div[4]//div/text()')

    markString = ''.join(marks)
    glyphString = ''.join(glyphs)
    sealString = ''.join(seals)
    quintString = ''.join(quints)

    runes = [markString, glyphString, sealString, quintString]
    return runes

client.run('MzEwOTM5MTYyMTg4NDQ3NzQ1.DFY9ag.yUPTBA-hQ-yypPHE-Uv_1br_iko')
