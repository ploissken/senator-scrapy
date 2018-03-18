FROM python:2

RUN mkdir /pol-scrapy
WORKDIR /pol-scrapy

ADD craw ./

RUN pip install -r requirements.txt

#CMD [ "python", "./my_script.py" ]