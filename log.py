#-*- coding: utf8 -*-
import logging

logger = logging.getLogger("http_proxy")
hdlr = logging.FileHandler("./log.log")
formatter = logging.Formatter(u'[%(asctime)s]%(levelname)-8s"%(message)s"','%Y-%m-%d %a %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)


