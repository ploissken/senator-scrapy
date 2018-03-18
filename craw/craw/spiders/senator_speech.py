import scrapy
import logging
from datetime import datetime

class FullSpeech():
    speech_link = ""
    speech_id = ""
    speech_date = ""
    speech_type = ""
    speech_location = ""
    speech_party = ""
    speech_summary = ""
    speech_full_text = ""

class SenatorSpeechCrawler(scrapy.Spider):


    global speeches_list
    speeches_list = []
    global year_count
    year_count = 0
    global speech_count
    speech_count = 0
    global base_url
    base_url = 'http://www25.senado.leg.br/web/atividade/pronunciamentos/-/p/parlamentar/%s'
    global text_url
    text_url = 'http://www25.senado.leg.br/web/atividade/pronunciamentos/-/p/texto/%s'
    global poli_id
    poli_id = "391"

    name = "senator-speech"
    start_urls = [base_url % "391"]

    def parse(self, response):
        #for each mandate year
        mandate_years = response.xpath('//div[@id="content"]//ul[@class="dropdown-menu"]//li')
        for speech_year in mandate_years.css('li a::attr(href)').extract():
            year = speech_year[speech_year.rfind('/')+1:len(speech_year)]
            global year_count
            year_count += 1
            request = scrapy.Request(response.url + "/" + year, callback=self.speech_parser)
            yield request

    #grab all the speech list info
    def speech_parser(self, response):
        for com in response.xpath('//div[@id="content"]//tbody//tr'):
            try:
                s = FullSpeech()
                i = 0 #lol
                #grab speech summary info
                s.speech_link = com.css('a::attr(href)').extract_first().encode('utf-8')
                i += 1
                s.speech_id = s.speech_link[s.speech_link.rfind('/')+1:len(s.speech_link)].encode('utf-8')
                i += 1
                s.speech_date = com.css('a::text').extract_first().encode('utf-8')
                i += 1
                s.speech_type = com.css('td::text')[0].extract().encode('utf-8')
                i += 1
                s.speech_location = com.css('td::text')[1].extract().encode('utf-8')
                i += 1
                s.speech_party = com.css('td::text')[2].extract().encode('utf-8')
                i += 1 
                #might not exist
                s.speech_summary = com.css('td::text')[3].extract().encode('utf-8')

            except IndexError:
                if i == 6:
                    logging.info('summary not found for speech (%s)' % s.speech_id)
                else:
                    logging.critical('parsing problem for speech (%s) at %s' % (s.speech_id, response.url))
            finally:
                global speeches_list
                speeches_list.append(s)

                global speech_count
                speech_count += 1

        next_page = response.css("div.pagination")
        for link in next_page.css('a').extract():
            link_text = link[link.find('>')+1:link.rfind('</a>')]
            last_link = ""
            if "xima" in link_text:
                next_link = link[link.find('"')+1:link.rfind('"')]
                re_quest =  scrapy.Request(next_link, callback=self.speech_parser)
                yield re_quest
            if "ltima" in link_text:
                last_link = link[link.find('"')+1:link.rfind('"')]
            if response.url == last_link:
                global year_count
                year_count -= 1

        #if all the mandate years's speech lists were crawled
        if year_count == 0:
            yield scrapy.Request("http://www25.senado.leg.br/", callback=self.parse_speech_text)
                        

    #grab each speech's full text
    def parse_speech_text(self, response):
        speech_file = open('json_data/%s_speech.json' % poli_id, 'wb')
        speech_file.write('{\n\t"json-ver": "0.1.0",\n\t"extraction-url": "%s",\n\t"extraction-datetime": "%s",\n\t"data": [\n' %
                (response.url, str(datetime.now())))
        for sp in speeches_list:
            request = scrapy.Request(text_url % sp.speech_id, dont_filter = True, callback=self.grab_speech_text)
            request.meta['speech'] = sp
            request.meta['speech_file'] = speech_file
            yield request

    def grab_speech_text(self, response):
        ss = response.meta['speech']
        s_file = response.meta['speech_file']
        speech_text = response.xpath('//div[@class="texto-integral"]/p/*/text() | //div[@class="texto-integral"]/p/*/*/text() | //div[@class="texto-integral"]/p/*/*/*/text()') #eheheh
        for p in speech_text.extract():
            ss.speech_full_text += (p.encode('utf-8') + "\n")

        if ss.speech_full_text == "":
            ss.speech_full_text = "Texto indisponivel".encode('utf-8')
        #print to file
        s_file.write('\t\t{"id": "%s",\n\t\t"link": "%s",\n\t\t"date": "%s",\n\t\t"type": "%s",\n\t\t"location": "%s",\n\t\t"party": "%s",\n\t\t"summary": "%s",\n\t\t"full-text": "%s"}' %
            (ss.speech_id, ss.speech_link, ss.speech_date, ss.speech_type, ss.speech_location, ss.speech_party, ss.speech_summary, ss.speech_full_text.replace('"', "'")))
        #global speeches_list
        #speeches_list.remove(ss)
        global speech_count
        speech_count -= 1

        if speech_count == 0:
            #close file
            s_file.write('\n\t]\n}')
        else:
            s_file.write(',\n')
            #logging.info(speeches_list[-1].speech_id)
            logging.info('speeches yet: %d, speech_count: %d' % (len(speeches_list), speech_count))

