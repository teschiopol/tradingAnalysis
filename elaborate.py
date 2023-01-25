import xlsxwriter
# import re
# import sys
# import datetime
# from time import sleep
from os import listdir
from os.path import isfile, join

unitColor = '\033[5;36m\033[5;47m'
endColor = '\033[0;0m\033[0;0m'
count = 45

'''
def data():

	# Open file txt to retrieve data
	filename_txt = "reports/CL_SYS 2018 @CL BRK HL0 30' OV nextday.txt"
	#filename_txt = "testo_ste.txt"
	file_txt = open(filename_txt, "r") # nome file o percorso
	list_txt = file_txt.readlines() # legge tutto il testo e lo salva in lista
	file_txt.close()

	# Create and insert data first report
	workbook = xlsxwriter.Workbook(filename_txt[:-3] + "xlsx")
	worksheet = workbook.add_worksheet('Data')

	row=0

	count=len(list_txt)
	time=datetime.datetime.now()

	for x in range(count):
		row_towrite = re.split("\s", list_txt[x])
		worksheet.write(row,0, row_towrite[0])
		worksheet.write(row,1, float(row_towrite[1]))
		worksheet.write(row,2, float(row_towrite[2]))
		worksheet.write(row,3, float(row_towrite[3]))
		worksheet.write(row,4, float(row_towrite[4]))
		worksheet.write(row,5, float(row_towrite[5]))
		row += 1
		incre = int(50.0 / count * x)
		sys.stdout.write('\r')
		sys.stdout.write('|%s%s%s%s| %d%%' % (unitColor, '\033[7m' + ' '*incre + ' \033[27m', endColor, ' '*(50-incre), 2*incre))
		sys.stdout.write(' ' + str(datetime.datetime.now()-time)[:7])
		sys.stdout.flush()
		sleep(0.1)
	workbook.close()
	sys.stdout.write('\nDONE\n')

if __name__ == '__main__':
	data()

'''

workbook = xlsxwriter.Workbook('proget.xlsx')  # nome file
worksheet1 = workbook.add_worksheet('unisci_equity')  # nome primo foglio
worksheet2 = workbook.add_worksheet('pivot')  # nome secondo figlio
worksheet3 = workbook.add_worksheet('single_drawdown')  # nome terzo foglio
worksheet4 = workbook.add_worksheet('single_equity')  # nome terzo foglio
worksheet5 = workbook.add_worksheet('ptf')  # nome terzo foglio

workbook.close()

mypath = 'reports/'

onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
print(onlyfiles)
