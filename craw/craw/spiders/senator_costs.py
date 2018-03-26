import scrapy
import logging
from datetime import datetime

class SenatorResourcesCrawler(scrapy.Spider):


    global year_count
    year_count = 0

    global base_url
    base_url = 'http://www6g.senado.leg.br/transparencia/sen/%s/?ano=%s#conteudo_transparencia'

    global poli_id
    poli_id = "391"

    name = "senator-resources"
    start_urls = [base_url % ("391", "2018")]

    def parse(self, response):
        res_file = open('json_data/%s_resources.json' % poli_id, 'wb')
        res_file.write('{\n\t"json-ver": "0.1.0",\n\t"extraction-url": "%s",\n\t"extraction-datetime": "%s",\n\t"data": [\n' %
                (response.url, str(datetime.now())))

        #for each mandate year
        logging.info("im awake, im awake...")
        mandate_years = response.xpath('//div[@id="conteudo_transparencia"]//ul[@class="dropdown-menu"]//li')
        for resources_year in mandate_years.css('li a::attr(href)').extract():
            year = resources_year[resources_year.rfind('=')+1:resources_year.rfind('#')]
            global year_count
            year_count += 1
            logging.info('got year %s' % year)
            request = scrapy.Request(base_url % (poli_id, year), callback=self.resources_parser)
            request.meta['res_file'] = res_file
            request.meta['year'] = year
            yield request

    #grab all the speech list info
    def resources_parser(self, response):

        year = response.meta['year']
        s_file = response.meta['res_file']

        #cotas para exercicio de atividade parlamentar
        for com in response.xpath('//div[@id="collapse-ceaps"]//tfoot//tr'):
            try:
                ceap_total = com.css('td::text')[1].extract().encode('utf-8')
            except IndexError:
                logging.info('summary not found for speech')
            finally:
                logging.info('done');

        #outros gastos
        for com in response.xpath('//div[@id="collapse-outros-gastos"]//tfoot//tr'):
            try:
                other_total = com.css('td::text')[1].extract().encode('utf-8')
            except IndexError:
                logging.info('summary not found for speech')
            finally:
                logging.info('done');


        ct = ceap_total.replace(".", "")        
        ot = other_total.replace(".", "")
        
        
        total = '%.2f' % (float(ct.replace(",", ".")) + float(ot.replace(",", ".")))

        #print to file
        s_file.write('\t\t{"year": "%s", "ceap": "%s", "other": "%s", "total": "%s"}' %
            (year, ceap_total, other_total, str(total)))

        global year_count
        year_count -= 1

        if year_count == 0:
            #close file
            s_file.write('\n\t]\n}')
        else:
            s_file.write(',\n')



                        

