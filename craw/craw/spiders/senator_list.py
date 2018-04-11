from datetime import datetime
import scrapy
import logging
import os

def mkdir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

class SenatorSpidey(scrapy.Spider):
    name = "senators-list"

    start_urls = [
        'http://www25.senado.leg.br/web/senadores/em-exercicio/-/e/por-nome',
    ]

    #parse list of elected senators
    def parse(self, response):
        mkdir('html_data')
        mkdir('json_data')
        filename = 'html_data/senators_list.html'
        fjson = open("json_data/senators_list.json", 'wb')
        with open(filename, 'wb') as f:
            fjson.write('{\n\t"json-ver": "0.1.0",\n\t"extraction-url": "%s",\n\t"extraction-datetime": "%s",\n\t"data": [\n' % (response.url, str(datetime.now())))
            senator_list = response.css('table tbody tr')
            for senator in senator_list:
                pol_name = senator.css('a::text').extract_first().encode('utf-8')
                pol_link = senator.css('a::attr(href)').extract_first().encode('utf-8')
                pol_party = senator.css('td::text').extract()[0].encode('utf-8')
                pol_state = senator.css('td::text').extract()[1].encode('utf-8')
                pol_id = pol_link[pol_link.rfind('/')+1:len(pol_link)]
                try:
                    if (len(senator.css('td::text').extract()) >= 4):
                        pol_email = senator.css('td::text').extract()[4].encode('utf-8')
                except:
                    pol_email = ''
                finally:
                    f.write(pol_id + " " + pol_name + " " + pol_party + " " + pol_state + " " + pol_email +'\n')
                    if senator is not senator_list[-1]:
                        fjson.write('\t\t{"name": "%s", "id": "%s", "party": "%s", "state": "%s", "email": "%s"},\n' %
                            (pol_name, pol_id, pol_party, pol_state, pol_email))
                    else:
                        fjson.write('\t\t{"name": "%s", "id": "%s", "party": "%s", "state": "%s", "email": "%s"}\n\t]\n}' %
                            (pol_name, pol_id, pol_party, pol_state, pol_email))
