FROM python:2

RUN mkdir -p /pol-scrapy/craw/
WORKDIR /pol-scrapy/craw/

ADD craw/requirements.txt ./
RUN pip install -r requirements.txt

ADD craw/* /pol-scrapy/craw/
