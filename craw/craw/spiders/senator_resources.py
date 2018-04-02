import scrapy
import json
import logging
from datetime import datetime

class SenatorResource():
    description = ""
    value = ""

class SenatorResourcesCrawler(scrapy.Spider):

    global ceap_list
    global other_list
    global ppl_list

    other_list = []
    ceap_list = []
    ppl_list = []

    global year_count
    year_count = 0

    global base_url
    base_url = 'http://www6g.senado.leg.br/transparencia/sen/%s/?ano=%s#conteudo_transparencia'

    global poli_id
    poli_id = "0"

    name = "senator-resources"
    start_urls = [base_url % (poli_id, "0")]

    def parse(self, response):
        #grab info for everyone (-a all=true)
        try:
            if(self.all):
                sen_list = json.load(open('json_data/senators_list.json'))
                for sen_id in sen_list['data']:
                    request = scrapy.Request(base_url % (sen_id['id'], "2018"), callback=self.resources_caller)
                    request.meta['p_id'] = sen_id['id']
                    yield request
        
        except AttributeError:
            #grab candidate info for variable id (-a pId=arg_id)
            try:
                request = scrapy.Request(base_url % (self.pId, "2018"), callback=self.resources_caller)
                request.meta['p_id'] = self.pId
                yield request


            except AttributeError:
                request = scrapy.Request(base_url % (poli_id, "2018"), callback=self.resources_caller)
                request.meta['p_id'] = poli_id
                yield request

    def resources_caller(self, response):
        p_id = response.meta['p_id']
        res_file = open('json_data/resources/%s.json' % p_id, 'wb')
        res_file.write('{\n\t"json-ver": "0.1.0",\n\t"extraction-url": "%s",\n\t"extraction-datetime": "%s",\n\t"data": [\n' %
                (response.url, str(datetime.now())))
        

        #for each mandate year
        mandate_years = response.xpath('//div[@id="conteudo_transparencia"]//ul[@class="dropdown-menu"]//li')
        logging.info(response.url)
        for resources_year in mandate_years.css('li a::attr(href)').extract():
            year = resources_year[resources_year.rfind('=')+1:resources_year.rfind('#')]
            logging.info("calling for " + year)
            global year_count
            year_count += 1
            request = scrapy.Request(base_url % (p_id, year), callback=self.resources_parser, dont_filter=True)
            request.meta['res_file'] = res_file
            request.meta['year'] = year
            yield request



    #grab all the resources list info
    def resources_parser(self, response):
        s_file = response.meta['res_file']
        year = response.meta['year']
        logging.info(response.url)
        logging.info("yeah for " + year)


        #cotas para exercicio de atividade parlamentar
        for res in response.xpath('//div[@id="collapse-ceaps"]//tbody//tr'):
            r = SenatorResource()
            descc = res.css('td::text')[0].extract().replace(u'\xa0', u'')
            r.description = descc.encode('utf-8').strip()
            r.value =  res.css('td a span::text')[0].extract().encode('utf-8').replace(".", "").replace(",", ".")
            global ceap_list
            ceap_list.append(r)

        for com in response.xpath('//div[@id="collapse-ceaps"]//tfoot//tr'):
            ceap_total = com.css('td::text')[1].extract().encode('utf-8')


        #outros gastos
        for res in response.xpath('//div[@id="collapse-outros-gastos"]//tbody//tr[@class="sen_tabela_linha_grupo"]'):
            r = SenatorResource()
            r.description = res.css('td::text')[0].extract().encode('utf-8').strip()
            r.value = ""
            r0 = ""
            r1 = ""
            r2 = ""
            try:
                r0 =  res.css('td[class=valor]::text')[0].extract().encode('utf-8')
                r1 = res.css('td[class=valor] a::text')[0].extract().encode('utf-8')
                r2 = res.css('td[class=valor] a span::text')[0].extract().encode('utf-8')
                
            except IndexError:
                try:
                    r1 = res.css('td[class=valor] a::text')[0].extract().encode('utf-8')
                except IndexError:
                    try:
                        r2 = res.css('td[class=valor] a span::text')[0].extract().encode('utf-8')
                    except:
                        pass
            finally:
                r.value = (r0+r1+r2).strip().replace(".", "").replace(",", ".")
                
                global other_list
                other_list.append(r)

        for com in response.xpath('//div[@id="collapse-outros-gastos"]//tfoot//tr'):
            other_total = com.css('td::text')[1].extract().encode('utf-8')


        #pessoal
        for res in response.xpath('//div[@id="collapse-pessoal"]//tbody//tr'):
            r = SenatorResource()
            r.description = res.css('td span::text')[0].extract().encode('utf-8')
            rarar = res.css('td a::text')[0].extract().replace(u'\xa0', u'').replace(" pessoa(s)", "").encode('utf-8')
            r.value = rarar
            global ppl_list
            ppl_list.append(r)



        ct = ceap_total.replace(".", "").replace(",", ".")
        ot = other_total.replace(".", "").replace(",", ".")
        
        
        

        #print it all to file
        for c_res in ceap_list:
            s_file.write('\t\t\t{"year": "%s", "type": "ceap", "description": "%s", "value": "%s"},\n' %
                (year.encode('utf-8'), c_res.description, c_res.value))

        for o_res in other_list:
            s_file.write('\t\t\t{"year": "%s", "type": "other", "description": "%s", "value": "%s"},\n' %
                (year.encode('utf-8'), o_res.description, o_res.value))


        for p_res in ppl_list:
            s_file.write('\t\t\t{"year": "%s", "type": "people", "description": "%s", "value": "%s"}' %
                (year.encode('utf-8'), p_res.description, p_res.value.split()))
            if(p_res == ppl_list[-1]):
                pass
            else:
                s_file.write(",\n")

        #cuz of duplication
        global ceap_list
        ceap_list = []
        global other_list
        other_list = []
        global ppl_list
        ppl_list = []

        global year_count
        year_count -= 1

        logging.info("*(*(*" + str(year_count))
        if year_count == 0:
            #close file
            s_file.write('\n\t]\n}')
        else:
            s_file.write(',\n')



                        

