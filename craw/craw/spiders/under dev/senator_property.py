import scrapy
import logging
 
 
class QuotesAjaxSpider(scrapy.Spider):
    name = 'senator-property'
    #https://noticias.uol.com.br/politica/politicos-brasil/resultado.htm?dados-cargo-disputado-id=05&ano-eleicao=all&next=0001H1115U15N
    base_url = 'https://noticias.uol.com.br/politica/politicos-brasil/resultado.htm?dados-cargo-disputado-id=05&ano-eleicao=all'
    start_urls = [base_url]
 
    def parse(self, response):
    	logging.info("**************************\n%s\n**************************" % response.xpath('//html').extract_first())
        for candidate in response.css('head'):
			logging.info("########/n%s/n#######" % candidate)
			cand_img = candidate.css('img::attr(src)').extract_first()
			link = candidate.css('a::attrs(href)').extract_first()
			cand_link = link[0:link.rfind('?')]
			cand_name = candidate.css('h1 a::text').extract_first()
			cand_party = candidate.css('h2 a::text').extract_first()
			logging.info("##### %s %s %s" % (cand_name, cand_party, cand_link))
