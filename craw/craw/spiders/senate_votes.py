from urlparse import urlparse
import scrapy
import logging
from tabula import read_pdf
import tabula

class SenateVotes(scrapy.Spider):
    name = "senate-votes"

    start_urls = [
        'http://www25.senado.leg.br/web/atividade/votacoes-nominais/-/v/periodo/08/02/2017/a/10/02/2017',
    ]

    def parse(self, response):
        filename = 'vote_sessions.html'
        with open(filename, 'wb') as f:
            for voting_session in response.css('table tbody tr'):
                try:
                    session_id = voting_session.css('td::text').extract()[0].encode('utf-8')
                    session_desc = voting_session.css('td::text').extract()[2].encode('utf-8')
                    session_votes_pdf = voting_session.css('a::attr(href)').extract_first().encode('utf-8')

                    #might not exist
                    session_spec = voting_session.css('span::text').extract()[0].encode('utf-8')
                except:
                    session_spec = ""
                finally:
                    f.write(session_id + " (" + session_spec + ")\n" + 
                        session_desc[0:25] + "...\n" + session_votes_pdf + "\n")
                    request = scrapy.Request(session_votes_pdf, callback=self.parse_pdf)
                    request.meta['s_id'] = session_id
                    yield request

    def parse_pdf(self, response):
        #local
        #df = read_pdf("votes.pdf", multiple_pages = True, pages="all", encoding="UTF-8")
        #remote should try
        session_id = response.meta['s_id']
        logging.critical("^^^^^^^ %s %s\n" % (session_id, response.url))
        df = read_pdf(response.url,
            multiple_pages = True, pages="all", encoding="UTF-8")

        fff = open("%s_votes.html" % session_id, 'wb')
        logging.critical("******\n")
        logging.critical(df)
        logging.critical("******")
        #df.applymap(lambda s: s.encode('utf-8'))

        for index, row in df.iterrows():
            senator_name = row[0]
            pdf_glitch = row[1]
            senator_state = row[2]
            senator_party = row[3]
            senator_vote = row[4]
            if senator_name != "SENADOR" and senator_name == senator_name:
                #senator_name.encode('utf-8')
                try:
                    s = senator_name
                    #logging.critical(senator_name)
                    #shift columns -1
                    if pdf_glitch == pdf_glitch:
                        senator_vote = senator_party
                        senator_party = senator_state
                        senator_state = pdf_glitch
                        #logging.critical(pdf_glitch)
                    #logging.critical(senator_state)
                    s += " "
                    s += senator_state
                    s += " "
                    s += senator_party
                    s += " "
                    s += senator_vote
                    #logging.critical(senator_party)
                    #if senator_vote == senator_vote:
                        #logging.critical(senator_vote)
                        
                    
                    #fff.write(senator_name.encode('utf-8') + " " + 
                    #    senator_party.encode('utf-8') + " " + 
                    #    senator_vote.encode('utf-8') + "\n")
                except:
                    logging.critical("excp parsing vote pdf - page break")
                finally:
                    logging.critical(s)

                    fff.write(s.encode('utf-8') + "\n")

        #tabula.convert_into("votes.pdf", "out.csv", output_format="csv")
            #logging.info(row['UF'])

        #fff.write(df);
        fff.close();
"""     path = "votes.pdf"
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        fp = file(path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos=set()

        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()

        fp.close()
        device.close()
        retstr.close()



        logging.critical(text)"""
