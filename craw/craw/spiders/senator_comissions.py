import scrapy
import logging
from datetime import datetime

class SenatorComissions(scrapy.Spider):
    name = 'senator-comissions'
    base_url = 'http://www25.senado.leg.br/web/senadores/senador/-/perfil/%s/comissoes/1'

    #aecim
    global poli_id
    poli_id = "391"

    start_urls = [base_url % "391"]

    
    def parse(self, response):
        json_file = open("json_data/%s_comm.json" % poli_id, 'wb')
        json_file.write('{\n\t"json-ver": "0.1.0",\n\t"extraction-url": "%s",\n\t"extraction-datetime": "%s",\n\t"data": [\n'
            % (response.url, str(datetime.now())))
        request = scrapy.Request(response.url, callback=self.parse_comissions)        
        request.meta['poli_id'] = poli_id
        request.meta['json_file'] = json_file
        yield request

    # recursively grab comissions info
    def parse_comissions(self, response):
        f = response.meta['json_file']

        comm_list = response.xpath('//tbody//tr') 
        for com in comm_list:
            try:
                com_link = com.css('a::attr(href)').extract_first().encode('utf-8')
                com_name = com.css('a::text').extract_first().encode('utf-8')
                com_start = com.css('td::text')[0].extract().encode('utf-8')
                com_end = com.css('td::text')[1].extract().encode('utf-8')
                com_function = com.css('td::text')[2].extract().encode('utf-8')
            except:
                logging.info("something wrong parsing comissions at %s" % response.url)
            finally:
                if com is not comm_list[-1]:
                    f.write('\t\t{"commision-name": "%s", "comission-link": "http:%s", "comission-function": "%s", "comission-start": "%s", "comission-end": "%s"},\n' %
                        (com_name, com_link, com_function, com_start, com_end))
                else:
                    f.write('\t\t{"commision-name": "%s", "comission-link": "http:%s", "comission-function": "%s", "comission-start": "%s", "comission-end": "%s"}' %
                        (com_name, com_link, com_function, com_start, com_end))


        next_page = response.css("div.pagination")
        last_link = ""
        for link in next_page.css('a').extract():
            if "xima" in link:
                next_link = link[link.find('"')+1:link.rfind('"')]
                #last page
                if response.url == next_link:
                    f.write('\n\t]\n}');
                #next page
                else:
                    f.write(',\n');
                    yield scrapy.Request(next_link,
                        callback=self.parse_comissions,
                        meta={'json_file': f})
    





