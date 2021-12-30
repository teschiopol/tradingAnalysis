# da terminale, python3 app.py
from flask import *
from sqlalchemy import *
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from models import *
from datetime import date, datetime, timedelta
import datetime
import math
import re
import random
import xlsxwriter

# dichairo app
app = Flask(__name__)

# variabile globale
app.jinja_env.globals['today'] = date.today().strftime("%d-%m-%Y")

# parametri da cambiare
position = 'localhost'
passwordDB = 'admin'
username = 'postgres'
'''
#creazione e connessione al database
engine = create_engine('postgresql+psycopg2://postgres:'+passwordDB+'@'+position+'/postgres')
conn = engine.connect()
conn.execute("commit")
try:
	conn.execute("create database ste")
except Exception:	
	print("errore di dio")
conn.close()
'''
uri = 'postgresql+psycopg2://'+username+':'+passwordDB+'@'+position+'/ste'
engine = create_engine(uri, echo=True)
metadata = MetaData()


#  colore che genero in modo randomico (hex)
def random_color_():
	r = random.randint(0,255)
	return r

# Homepage
@app.route('/')
def home():
	conn = engine.connect()
	reports = conn.execute('SELECT * FROM reports ORDER BY name ')
	reports = list(reports)
	conn.close()
	return render_template('index.html', reports=reports, res='', n_report=0, tot_report=len(reports))


@app.route('/cerca', methods=['GET', 'POST'])
def ricerca():
	conn = engine.connect()
	list_report = request.form.getlist('col')
	data_dal = request.form['dal']
	data_al = request.form['al']
	flagdario = request.form['flagDario']
	numero_contratti = request.form['n_contratti']
	numero_contratti = round(float(numero_contratti))
	if float(numero_contratti) < 1.0:
		numero_contratti = 1.0
	if  list_report == [] or list_report[0] == '':
		rep = conn.execute('SELECT name,id from reports order by name')
	else:	
		rep = conn.execute(select([reports.c.name,reports.c.id],reports.c.id.in_(list_report)).order_by(reports.c.name))
	rep_iter = list(rep)
	rep_iter_single = []
	for d in rep_iter:
		rep_iter_single.append(d[1])
	if data_al == '':
		data_al =  date.today().strftime("%Y-%m-%d")
		data_final = conn.execute(select([func.max(dati.c.data).label('maxdata')], dati.c.idreport.in_(rep_iter_single)))
		data_al = str(data_final.fetchone()['maxdata'])
		data_al = datetime.datetime(int(data_al[:4]), int(data_al[5:7]), int(data_al[8:10])).strftime("%Y-%m-%d")
	if data_dal == '':
		data_dal =  datetime.datetime(2018, 1, 1).strftime("%Y-%m-%d")
		data_final = conn.execute(select([func.min(dati.c.data).label('mindata')], dati.c.idreport.in_(rep_iter_single)))
		data_dal = str(data_final.fetchone()['mindata'])
		data_dal = datetime.datetime(int(data_dal[:4]), int(data_dal[5:7]), int(data_dal[8:10])).strftime("%Y-%m-%d")
	
	data_final = conn.execute('SELECT max(data) as maxdata from dati')
	data_final = str(data_final.fetchone()['maxdata'])
	app.jinja_env.globals['today'] = datetime.datetime(int(data_final[:4]), int(data_final[5:7]), int(data_final[8:10])).strftime("%Y-%m-%d")
		
	res = conn.execute(select([func.sum(dati.c.daily_profit_loss), dati.c.data, func.max(dati.c.somma_trade),dati.c.anno, dati.c.mese ],dati.c.idreport.in_(rep_iter_single)).where(and_(dati.c.data >= data_dal, dati.c.data <= data_al)).group_by(dati.c.data,dati.c.anno,dati.c.mese).order_by(dati.c.data))	
	pivot_data = list(res)
	unisci_data = pivot_data
	report = conn.execute('SELECT * FROM reports order by name')
	mes_ann = conn.execute(select([func.sum(dati.c.daily_profit_loss), dati.c.anno, dati.c.mese, func.min(dati.c.daily_profit_loss), func.max(dati.c.daily_profit_loss), func.avg(dati.c.daily_profit_loss) ],dati.c.idreport.in_(rep_iter_single)).where(and_(dati.c.data >= data_dal, dati.c.data <= data_al)).group_by(dati.c.anno, dati.c.mese).order_by(dati.c.anno, dati.c.mese))	
	conn.close()
	mes_ann = list(mes_ann)
	report = list(report)
	sup_report = [[]]
	for x in report:
		sup_report.append([x.id, x.name, 0])
	sup_report.pop(0)
	if  list_report != [] and list_report[0] != '':
		for x in sup_report:
			if str(x[0]) in list_report:
				x[2] = 1

	# drawdown
	drawdown_first = 0
	drawdown_max = 0
	drawdown_sum = 0
	drawdown_list = [[]]
	num_op = 0
	acc = pivot_data[0][2]
	mesi = [['Gennaio',31], ['Febbraio',28], ['Marzo',31], ['Aprile',30], ['Maggio',31], ['Giugno',30], ['Luglio',31], ['Agosto',31], ['Settembre',30], ['Ottobre',31], ['Novembre',30], ['Dicembre',31]]
	mese = 	pivot_data[0][1].strftime("%-m") 
	for d in pivot_data:
		if 	d[1].strftime("%-m") == mese:
			num_op = d[2] - acc
		drawdown_prev = drawdown_first + (d[0] * numero_contratti)
		drawdown_final = 0
		if drawdown_prev < 0:
			drawdown_sum += drawdown_prev
			drawdown_final = drawdown_prev
		drawdown_first = drawdown_final
		if drawdown_max > drawdown_first:
			drawdown_max = drawdown_first
		if 	d[1].strftime("%-m") != mese:
			drawdown_list.append([drawdown_max, round((drawdown_sum/mesi[int(mese)-1][1]),2), num_op])
			acc += num_op
			drawdown_first = 0
			drawdown_max = 0
			drawdown_sum = 0
			mese = d[1].strftime("%-m")

	ttr_min=0.00
	ttr_max=0.00
	ttr_time=0
	ttr_time_max=0
	ttr_equity = 0.0
	ttr = []
	ttr_medio = []
	ttr_acc = 0
	ttr_div = 0
	ttr_mese=pivot_data[0][1].strftime("%-m")
	for d in pivot_data:
		if d[1].strftime("%-m") != ttr_mese:
			ttr.append(ttr_time_max)
			if ttr_div == 0:
				ttr_acc = 0
			else :	
				ttr_acc = ttr_acc / ttr_div;
			ttr_medio.append(ttr_acc)
			ttr_acc = 0
			ttr_div = 0
			ttr_mese = d[1].strftime("%-m")
			ttr_min=0.00
			ttr_max=0.00
			ttr_time=0
			ttr_time_max=0
			ttr_equity = 0.0
		if ttr_equity > ttr_max:
			ttr_max = ttr_equity
			if ttr_time > ttr_time_max:
				ttr_time_max = ttr_time
			ttr_div += 1
			ttr_acc += ttr_time	
			ttr_min = 0
		if ttr_equity < ttr_min:
			ttr_min = ttr_equity
		if ttr_equity >= ttr_min and ttr_equity < ttr_max:
			ttr_time += 1				
		ttr_equity += (d[0]* numero_contratti)
	ttr_medio.append(ttr_acc)
	ttr.append(ttr_time_max)
	drawdown_list.pop(0)
	html_sup = sup_report
	drawdown_list.append([drawdown_max, round((drawdown_sum/mesi[int(mese)-1][1]),2), num_op])

	'''
	# Create and insert data first report
	workbook = xlsxwriter.Workbook("RB_SYS SIMPLY 2018 @RB BRK HL1 5' OV weekly.xlsx")
	worksheet = workbook.add_worksheet('Data')
	worksheet.write(0,0, 'Date' )
	worksheet.write(0,1, 'Equity')
	worksheet.write(0,3, 'Average Trade')
	
	row=1
	index=0
	for l in mes_ann:
		worksheet.write(row,0, mesi[(l[2])-1][0])
		worksheet.write(row,1, l[0])
		if drawdown_list[index][2] == 0:
			ele = 0
		else:	
			ele = l[0]/drawdown_list[index][2]
		worksheet.write(row,3, ele)
		index += 1
		row += 1
	workbook.close()
	'''

	return render_template('index.html', reports=report, rep = rep_iter, res=unisci_data, dal=data_dal , al =data_al, anni = mes_ann, mesi=mesi, len=len(mes_ann), dd=drawdown_list, ttr = ttr, ttr_medio = ttr_medio, molt = numero_contratti, html_sup = html_sup, n_report=len(rep_iter), tot_report=len(report), darietto=flagdario)

@app.route('/plot', methods=['GET', 'POST'])
def graph():
	conn = engine.connect()
	url = request.full_path
	url = url[6:]
	dataI=url[6:16]
	dataF= url[23:33]
	contratti=url[42:43]
	strategie=url[54:]
	strategie = strategie.split(",")
	mesi_nome = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre']
	master_ret = [[]]
	if strategie[0] == '0':
		res = conn.execute(select([func.sum(dati.c.daily_profit_loss), dati.c.anno, dati.c.mese ]).where(and_(dati.c.data >= dataI, dati.c.data <= dataF)).group_by(dati.c.anno,dati.c.mese).order_by(dati.c.anno,dati.c.mese))	
		strategie = conn.execute(select([reports.c.id]))
		strategie_int = list(strategie)
		strategie = []
		for e in strategie_int:
			strategie.append(e[0])
		for x in strategie:
			sup_query = conn.execute(select([func.sum(dati.c.daily_profit_loss), dati.c.anno, dati.c.mese ]).where(and_(dati.c.data >= dataI, dati.c.idreport == x, dati.c.data <= dataF)).group_by(dati.c.anno,dati.c.mese).order_by(dati.c.anno,dati.c.mese))
			sup_query = list(sup_query)
			master_ret.append(sup_query)
		nome_sup_query = conn.execute(select([reports.c.id, reports.c.name], reports.c.id.in_(strategie)))
		nome_sup_query =  list(nome_sup_query)
	else:
		for x in strategie:
			sup_query = conn.execute(select([func.sum(dati.c.daily_profit_loss), dati.c.anno, dati.c.mese ]).where(and_(dati.c.data >= dataI, dati.c.idreport == x, dati.c.data <= dataF)).group_by(dati.c.anno,dati.c.mese).order_by(dati.c.anno,dati.c.mese))
			sup_query = list(sup_query)
			master_ret.append(sup_query)
		nome_sup_query = conn.execute(select([reports.c.id, reports.c.name], reports.c.id.in_(strategie)))
		nome_sup_query =  list(nome_sup_query)
		res = conn.execute(select([func.sum(dati.c.daily_profit_loss), dati.c.anno, dati.c.mese ],dati.c.idreport.in_(strategie)).where(and_(dati.c.data >= dataI, dati.c.data <= dataF)).group_by(dati.c.anno,dati.c.mese).order_by(dati.c.anno,dati.c.mese))	
	
	res_all = list(res)
	master_ret.append(res_all)
	master_ret.pop(0)
	# ho una lista che per ogni posizione ha una lista di array [valore, anno, mese]
	# devo avere nome + dati + colore
	# faccio array valori per ognuno
	new_array = [[]]
	dd_array = [[]]
	j = 0
	for v in master_ret:
		i=0
		start = 0
		att = 0
		sup_insert = []
		sub_insert = []
		somma_insert = [[]]
		dd_insert = [[]]
		nome_insert = []
		color_insert = []
		summa = 0
		while (i < len(v)):
			att = summa
			summa += v[i][0]
			sup_insert.append(summa)
			if summa < att:
				start = att-summa
				sub_insert.append(-start)
			else:
				sub_insert.append(-start)
			i += 1
		if j < len(strategie):
			nome_insert.append( nome_sup_query[j][1].replace("'", '') )
			j += 1
			color_insert.append(random_color_())
			color_insert.append(random_color_())
			color_insert.append(random_color_())
		else:
			nome_insert.append('ALL SYSTEM')
			color_insert.append(0)
			color_insert.append(0)
			color_insert.append(0)
		somma_insert.append(sup_insert)
		somma_insert.append(sub_insert)
		somma_insert.append(nome_insert)
		somma_insert.append(color_insert)
		somma_insert.pop(0)
		dd_insert.append(sub_insert)
		dd_insert.append(nome_insert)
		dd_insert.append(color_insert)
		dd_insert.pop(0)
		new_array.append(somma_insert)
		dd_array.append(dd_insert)
	new_array.pop(0)
	dd_array.pop(0)
	# lista mesi
	mesi = []
	sup_mes = res_all[0][1]
	for x in res_all:
		if (sup_mes != x[1]):
			mesi.append(x[1])
			sup_mes = x[1]
		else:	
			mesi.append(mesi_nome[x[2]-1])
	mesi2 = mesi	
	conn.close()
	return render_template('plot.html', sup=new_array, lab = mesi, ddlab = mesi2, ddd = dd_array)

@app.route('/dario', methods=['GET', 'POST'])
def darietto():
	conn = engine.connect()
	url = request.full_path
	url = url[7:]
	dataI=url[6:16]
	dataF= url[23:33]
	contratti=url[42:43]
	strategie=url[54:]
	strategie = strategie.split(",")
	if strategie[0] == '0':
		nome_sup_query = conn.execute(select([reports.c.id, reports.c.name]))
		strategie =  list(nome_sup_query)
	else:
		nome_sup_query = conn.execute(select([reports.c.id, reports.c.name], reports.c.id.in_(strategie)))
		strategie =  list(nome_sup_query)
	conn.close()

	# 
	# chiamo PlotEquity sui soli file che ho scelto
	# apro csv onOff e prendo solo quelli con determinati valori
	

	return render_template('dario.html', strategie = strategie, da=dataI , a=dataF, contratti = contratti)

@app.route('/intermediate', methods=['GET', 'POST'])
def mid():
	conn = engine.connect()
	url = request.full_path
	url = url[14:]
	dataI=url[6:16]
	dataF= url[23:33]
	contratti=url[42:43]
	strategie=url[54:]
	strategie = strategie.split(",")
	if strategie[0] == '0':
		nome_sup_query = conn.execute(select([reports.c.id, reports.c.name]))
		strategie =  list(nome_sup_query)
	else:
		nome_sup_query = conn.execute(select([reports.c.id, reports.c.name], reports.c.id.in_(strategie)))
		strategie =  list(nome_sup_query)
	conn.close()
	return render_template('mid.html', strategie = strategie, da=dataI , a=dataF, contratti = contratti)
# main
if __name__ == '__main__':
	app.run(debug=True)

