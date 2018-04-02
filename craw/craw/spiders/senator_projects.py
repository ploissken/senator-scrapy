import scrapy
import logging
from datetime import datetime

class SenatorProjects(scrapy.Spider):
    name = 'senator-projects'
    base_url = 'http://www25.senado.leg.br/web/atividade/materias/-/materia/autor/%s/p/1/o/1'
    
    #aecim
    global poli_id
    poli_id = "3398"

    start_urls = [base_url % poli_id]

    
    def parse(self, response):
        json_file = open("json_data/%s_proj.json" % poli_id, 'w')
        json_file.write('{\n\t"json-ver": "0.1.0",\n\t"extraction-url": "%s",\n\t"extraction-datetime": "%s",\n\t"data": [\n'
            % (response.url, str(datetime.now())))
        request = scrapy.Request(response.url, callback=self.parse_authorship)        
        request.meta['json_file'] = json_file
        yield request

    # recursively grab projects info
    def parse_authorship(self, response):
        f = response.meta['json_file']

        proj_list = response.xpath('//div[@class="div-zebra"]//div//dl')
        for proj in proj_list:
            try:
                proj_link = proj.css('a::attr(href)').extract_first().encode('utf-8')
                proj_id = proj.css('span::text').extract_first().encode('utf-8')

                # FIXME: works... but its ugly as hell
                p_de = proj.css('dd')[1].extract()
                proj_desc = p_de[p_de.find('<dd>')+4:p_de.rfind('</dd>')].encode('utf-8')
                proj_desc = proj_desc.replace('"', "'")
                p_au = proj.css('dd')[2].extract()
                proj_authors = p_au[p_au.find('<dd>')+4:p_au.rfind('</dd>')].encode('utf-8')
                p_da = proj.css('dd')[3].extract()
                proj_date = p_da[p_da.find('<dd>')+4:p_da.rfind('</dd>')].encode('utf-8')

            except:
                logging.critical("something wrong parsing projects authorship for poli_id: %s proj_id: %s" % (poli_id, proj_id))
            
            finally:
                if proj is not proj_list[-1]:
                    f.write('\t\t{"project-id": "%s", "project-description": "%s", "project-link": "%s", "project-date": "%s", "project-authors": "%s" },\n' %
                        (proj_id, proj_desc, proj_link, proj_date, proj_authors))
                else:
                    f.write('\t\t{"project-id": "%s", "project-description": "%s", "project-link": "%s", "project-date": "%s", "project-authors": "%s" }' %
                        (proj_id, proj_desc, proj_link, proj_date, proj_authors))


        pagination = response.css("div.pagination")
        pag_links = pagination.css('a').extract()
        last_page_found = False
        for link in pag_links:
            if "ltima" in link: last_page_found = True
            if "xima" in link:
                next_link = link[link.find('"')+1:link.rfind('"')]
                f.write(',\n');
                logging.info('crawling next page: %s' % next_link)
                yield scrapy.Request(next_link, callback=self.parse_authorship,
                    meta={'json_file': f, 'poli_id': poli_id})
        
        if last_page_found is False:
            #this is the last page, close file
            f.write('\n\t]\n}')
    

