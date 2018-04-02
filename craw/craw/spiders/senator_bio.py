import scrapy
import logging
import os
import json
from datetime import datetime

class SenatorBiography(scrapy.Spider):
    name = 'senator-bio'
    global base_url
    base_url = 'http://www25.senado.leg.br/web/senadores/senador/-/perfil/%s'
    
    #aecim
    global pol_id
    pol_id = "3398" #3398, 391 cristovam, aecio

    start_urls = [base_url % pol_id]




    
    def parse(self, response):
        # grab all candidates info
        try:
            if(self.all):   
                sen_list = json.load(open('json_data/senators_list.json'))
                for sen_id in sen_list['data']:
                    #logging.info(sen_id['id'])
                    request = scrapy.Request(base_url % sen_id['id'], callback=self.parse_bio)
                    request.meta['pol_name'] = sen_id['name'].encode('utf-8')
                    request.meta['p_id'] = sen_id['id']
                    yield request

        except AttributeError:
            pass

        #grab candidate info for variable id (-a pId=arg_id)
        try:
            request = scrapy.Request(base_url % self.pId, callback=self.parse_bio)
            request.meta['pol_name'] = "FIXME"
            request.meta['p_id'] = self.pId
            yield request
        
        except AttributeError:
            #grab bio for poli_id
            request = scrapy.Request(base_url % pol_id, callback=self.parse_bio)
            request.meta['pol_name'] = "FIXME"
            request.meta['p_id'] = pol_id
            yield request




    def parse_bio(self, response):
        pol_name = response.meta['pol_name']
        p_id = response.meta['p_id']
        htmlfile = "html_data/%s_bio.html" % p_id
        jsonfile = open("json_data/bio/%s.json" % p_id, 'wb')
        with open(htmlfile, 'wb') as f:
            jsonfile.write('{\n\t"json-ver": "0.1.0",\n\t"extraction-url": "%s",\n\t"extraction-datetime": "%s",\n\t"data": {\n' %
                (response.url, str(datetime.now())))
            for personal_info in response.css('dl.dl-horizontal'):
                pol_full_name = personal_info.css('dd::text').extract()[0].encode('utf-8')
                pol_bday = personal_info.css('dd::text').extract()[1].encode('utf-8')
                pol_bplace = personal_info.css('dd::text').extract()[2].encode('utf-8')
                f.write("%s\n%s\n%s\n" % (pol_full_name, pol_bday, pol_bplace))
                jsonfile.write('\t\t"full-name": "%s",\n\t\t"pop-name": "%s",\n\t\t"birthday": "%s",\n\t\t"hometown": "%s",\n' %
                    (pol_full_name, pol_name, pol_bday, pol_bplace))

            #http://www.senado.gov.br/senadores/img/fotos-oficiais/@pol_id
            pol_pic = response.css("div.foto img::attr(src)").extract_first().encode('utf-8')
            f.write(p_id + "\n" + pol_pic + "\n")
            jsonfile.write('\t\t"picture-url": "%s",\n' % pol_pic)
            
            #suplentes por mandato
            #TODO: grab suplente id, if any 
            mandate_suplentes = response.xpath("//div[@id='accordion-chapa']//div//div//div[@id]")
            #logging.critical(mandate_suplentes)

            #missoes nacionais
            br_missions = response.xpath("//div[@id='missoes']//div//div[2]")
            mission_list = br_missions.css('tr')
            jsonfile.write('\t\t"national-missions": [\n')
            if len(mission_list) > 0:
                for mission in mission_list:
                    if mission.css('td').extract_first() is not None:
                        mission_summary = mission.css('td::text')[0].extract().encode('utf-8').replace('"', "'")
                        mission_start = mission.css('span::text')[0].extract().encode('utf-8')
                        mission_doc = mission.css('td::text')[3].extract().encode('utf-8')
                        mission_end = ""
                        try:
                            mission_end = mission.css('span::text')[1].extract().encode('utf-8')
                        except:
                            logging.info("single day national mission found for id %s" % p_id)
                        finally:
                            if mission is not mission_list[-1]:
                                jsonfile.write('\t\t\t{"mission-summary": "%s", "mission-start": "%s", "mission-end": "%s", "mission-doc": "%s"},\n' %
                                    (mission_summary, mission_start, mission_end, mission_doc))
                            else:
                                jsonfile.write('\t\t\t{"mission-summary": "%s", "mission-start": "%s", "mission-end": "%s", "mission-doc": "%s"}\n\t\t],\n' %
                                    (mission_summary, mission_start, mission_end, mission_doc))
            else:
                jsonfile.write('\t\t],\n');


            #missoes internacionais
            ext_missions = response.xpath("//div[@id='missoes']//div//div[1]")
            
            int_mission_list = ext_missions.css('tr')
            jsonfile.write('\t\t"international-missions": [\n')
            if len(int_mission_list) > 0:
                for mission in int_mission_list:
                    if mission.css('td').extract_first() is not None:
                        mission_summary = mission.css('td::text')[0].extract().encode('utf-8').replace('"', "'")
                        mission_start = mission.css('span::text')[0].extract().encode('utf-8')
                        mission_doc = mission.css('td::text')[3].extract().encode('utf-8')
                        mission_end = ""
                        try:
                            mission_end = mission.css('span::text')[1].extract().encode('utf-8')
                        except:
                            logging.info("single day international mission found for id %s" % p_id)
                        finally:
                            if mission is not int_mission_list[-1]:
                                jsonfile.write('\t\t\t{"mission-summary": "%s", "mission-start": "%s", "mission-end": "%s", "mission-doc": "%s"},\n' %
                                    (mission_summary, mission_start, mission_end, mission_doc))
                            else:
                                jsonfile.write('\t\t\t{"mission-summary": "%s", "mission-start": "%s", "mission-end": "%s", "mission-doc": "%s"}\n\t\t],\n' %
                                    (mission_summary, mission_start, mission_end, mission_doc))
            else:
                jsonfile.write('\t\t],\n');

            #biografia academica
            bio_academic = response.xpath('//div[@id="accordion-biografia"]//div//table[1]//tbody')
            
            first_header = response.xpath('//div[@id="accordion-biografia"]//div')
            first_header = first_header.css('h3::text').extract_first()

            #historico academico
            jsonfile.write('\t\t"academic-list": [\n')
            if "rico Acad" in first_header:
                acad_list = bio_academic.css('tr')
                for academic_info in acad_list:
                    if academic_info.css('td').extract_first() is not None:
                        acad_course = academic_info.css('td::text')[0].extract().encode('utf-8')
                        acad_grad = academic_info.css('td::text')[1].extract().encode('utf-8')
                        acad_school = academic_info.css('td::text')[2].extract().encode('utf-8')
                        acad_place = academic_info.css('td::text')[3].extract().encode('utf-8')
                        f.write("%s %s %s %s\n" % (acad_course, acad_grad, acad_school, acad_place))    
                        if academic_info is not acad_list[-1]:
                            jsonfile.write('\t\t\t{"course": "%s", "degree": "%s", "institution": "%s", "location": "%s"},\n' %
                                (acad_course, acad_grad, acad_school, acad_place))
                        else:
                            jsonfile.write('\t\t\t{"course": "%s", "degree": "%s", "institution": "%s", "location": "%s"}\n\t\t],\n' %
                                (acad_course, acad_grad, acad_school, acad_place))    
            else:
                jsonfile.write('\t\t],\n');

            #carreira
            bio_profession = response.xpath('//div[@id="accordion-biografia"]//div//ul')
            
            prof_list = bio_profession.css('li')
            jsonfile.write('\t\t"profession-list": [')
            if len(prof_list) > 0:
                for profession in prof_list:
                    if profession.css('span::text').extract_first() is not None:
                        p = profession.css('span::text').extract_first().encode('utf-8')
                        f.write(p + "\n")
                        if profession is not prof_list[-1]:
                            jsonfile.write('"%s", ' % p)
                        else:
                            jsonfile.write('"%s"],\n' % p)
            else:
                jsonfile.write('],\n');

            #mandatos anteriores
            if "Mandatos" in first_header:
                jsonfile.write('\t\t"past-mandates": [\n')
                mandate_list = bio_academic.css('tr')
                for mand in mandate_list:
                    if mand.css('td').extract_first() is not None:
                        mand_type = mand.css('td::text')[0].extract().encode('utf-8')
                        mand_start = mand.css('td::text')[1].extract().encode('utf-8')
                        mand_end = ""
                        try:
                            #mandate might not have end yet
                            mand_end = mand.css('td::text')[2].extract().encode('utf-8')
                        except:
                            logging.info("found mandate not finished (%s)" % p_id)
                        finally:
                            f.write("%s\n%s\n%s\n" % (mand_type, mand_start, mand_end))
                            if mand is not mandate_list[-1]:
                                jsonfile.write('\t\t\t{"mandate-type": "%s", "mandate-start": "%s", "mandate-end": "%s"},\n' %
                                    (mand_type, mand_start, mand_end))
                            else:
                                jsonfile.write('\t\t\t{"mandate-type": "%s", "mandate-start": "%s", "mandate-end": "%s"}\n\t\t]\n' %
                                    (mand_type, mand_start, mand_end))

            else:
                past_mandates =  response.xpath('//div[@id="accordion-biografia"]//div//table[2]//tbody')
                jsonfile.write('\t\t"past-mandates": [\n')
                mandate_list = past_mandates.css('tr')
                for mand in mandate_list:
                    if mand.css('td').extract_first() is not None:
                        mand_type = mand.css('td::text')[0].extract().encode('utf-8')
                        mand_start = mand.css('td::text')[1].extract().encode('utf-8')
                        mand_end = ""
                        try:
                            #mandate might not have end yet
                            mand_end = mand.css('td::text')[2].extract().encode('utf-8')
                        except:
                            logging.info("found mandate not finished (%s)" % p_id)
                        finally:
                            f.write("%s\n%s\n%s\n" % (mand_type, mand_start, mand_end))
                            if mand is not mandate_list[-1]:
                                jsonfile.write('\t\t\t{"mandate-type": "%s", "mandate-start": "%s", "mandate-end": "%s"},\n' %
                                    (mand_type, mand_start, mand_end))
                            else:
                                jsonfile.write('\t\t\t{"mandate-type": "%s", "mandate-start": "%s", "mandate-end": "%s"}\n\t\t]\n' %
                                    (mand_type, mand_start, mand_end))

            jsonfile.write('\t}\n}')
