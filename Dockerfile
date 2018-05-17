FROM python:2

RUN mkdir -p /pol-scrapy/craw/
WORKDIR /pol-scrapy/craw/

RUN mkdir -p json_data/bio json_data/resources json_data/projects

ADD craw/requirements.txt ./
RUN pip install -r requirements.txt

ADD craw/* /pol-scrapy/craw/
