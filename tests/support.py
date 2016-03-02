from os.path import join, dirname
from dotenv import load_dotenv
import logging

dotenv_path = join(dirname(__file__), '../.env.test')
load_dotenv(dotenv_path)

from farnsworth import *
from farnsworth.config import db

# logger = logging.getLogger('peewee')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())

def truncate_tables():
    tables = [
        Bitmap,
        ChallengeBinaryNode,
        Crash,
        Exploit,
        Job,
        Pcap,
        Performance,
        Round,
        Score,
        Team,
        Test,
    ]
    table_names = map(lambda t: t._meta.db_table, tables)
    db.execute_sql("TRUNCATE {} RESTART IDENTITY CASCADE".format(", ".join(table_names)))
