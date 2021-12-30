from sqlalchemy import *
from app import engine, metadata
from os import listdir
from os.path import isfile, join
import re
import datetime

mypath = 'reports/'

onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
onlyfiles = onlyfiles[1:]


# creazione tabelle
reports = Table('reports', metadata,
	Column('id', Integer, primary_key = True),
	Column('name', String)
)

dati = Table('dati', metadata,
	Column('id', Integer, primary_key = True),
	Column('idreport', Integer),
	Column('data', Date),
	Column('daily_profit_loss', Float),
	Column('n_contratti', Integer),
	Column('gap', Float),
	Column('daily_range', Float),
	Column('somma_trade', Integer),
	Column('mese', Integer),
	Column('anno', Integer)
)

'''
#inizializzo database e creo tabelle
metadata.drop_all(engine)
metadata.create_all(engine)

# popolo il database con le insert
ins = reports.insert()
insData = dati.insert()
conn = engine.connect()

index = 1
#insert
for r in onlyfiles:
	conn.execute(ins,[
		{'name': r[:-4]},
	])
	
	filename_txt = r
	file_txt = open('reports/' + filename_txt, "r") # nome file o percorso
	list_txt = file_txt.readlines() # legge tutto il testo e lo salva in lista
	file_txt.close()
	count=len(list_txt)
	for x in range(count):
		row_towrite = re.split("\s", list_txt[x])
		data_time = datetime.datetime(int(row_towrite[0][-4:]), int(row_towrite[0][3:5]), int(row_towrite[0][:2]))
		conn.execute(insData,[
			{'idreport': index,'data': data_time,'daily_profit_loss': row_towrite[1],'n_contratti': row_towrite[2],'gap': row_towrite[3],'daily_range': row_towrite[4],'somma_trade': row_towrite[5], 'mese': int(row_towrite[0][3:5]), 'anno': int(row_towrite[0][-4:]) }
		])

	index += 1

conn.close()
'''
