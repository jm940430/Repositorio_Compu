#!/usr/bin/python
#-*-coding:utf-8-*-

import urllib2
import re
import time
from pymongo import MongoClient
from beebotte import *
from flask import Flask, render_template, request, redirect
from apscheduler.schedulers.background import BackgroundScheduler

app=Flask(__name__)
url_numeros = 'http://www.numeroalazar.com.ar/'
url_grafica = 'https://beebotte.com/dash/0bdac7d0-cefb-11e7-bfef-6f68fef5ca14#.Wh3Wh_aIbCI'
Pass1='84c0e7fa36f3acbb9baa4a47ccfa8b95'
Pass2='2f574d96af2b74a7fc78daaf45ac349eebcb4f55214490705c136ef58f925dd2'
flagMongo=True


def obtener_numero():
	global NumeroGuardar
	#Acceso Página y obtencion del numero
	pagina_url = urllib2.urlopen(url_numeros)
	aleatorios = pagina_url.read()
	NumerosObtenidos = re.findall('\d+\.\d*',aleatorios)
	NumeroGuardar = float(NumerosObtenidos[4])


def obtener_acceso():
	global AccesoGuardar
	acceso = time.asctime(time.localtime(time.time()))
	AccesoGuardar = acceso


def guardar_DB():
	# MongoDB
	cliente = MongoClient()
	db = cliente['DBnumeros']
	diccionario = {'aleatorio': NumeroGuardar,
			'hora': AccesoGuardar}
	AleatoriosDB = db['AletaoriosDB']
	AleatoriosDB.insert_one(diccionario)
	# BeeBotte DB
	clienteBBT = BBT(Pass1,Pass2)
	numerosBBT = Resource(clienteBBT,'Random_Numbs','numb_input')
	numerosBBT.write(NumeroGuardar)
	print 'Numero: ' + str(NumeroGuardar)
	print AccesoGuardar

def obtener_datos():
	obtener_numero()
	obtener_acceso()
	guardar_DB()

def calcular_media():
	global flagMongo
	global mediaT
	listaBBT = []
	if flagMongo:
		cliente = MongoClient()
		db = cliente['DBnumeros']
		AleatoriosDB = db['AletaoriosDB']
		aleatoriosMedia = AleatoriosDB.find()
		calcularMedia=0
		for aleatorio in aleatoriosMedia:
			calcularMedia+=float(aleatorio['aleatorio'])
		numelem = aleatoriosMedia.count()
		mediaT = '%0.2f obtenido de MongoDB' %(calcularMedia/numelem)
		flagMongo=False
	else:
		clienteBBT = BBT(Pass1,Pass2)
		aleatoriosBBT = clienteBBT.read('Random_Numbs','numb_input',limit=50000)
		for aleatorio2 in aleatoriosBBT:
			listaBBT.append(aleatorio2['data'])
		calcularMedia2=sum(listaBBT)
		numelmBBT=len(listaBBT)
		mediaT = '%0.2f obtenido de BeeBotteDB' %(calcularMedia2/numelmBBT)
		flagMongo=True
		

def umbral_inferior(umbral):
	global menorMostrar
	menor=[]
	cliente = MongoClient()
	db = cliente['DBnumeros']
	AleatoriosDB = db['AletaoriosDB']
	aleatoriosInferior = AleatoriosDB.find({'aleatorio':{'$lt':float(umbral)}})
	for inferior in aleatoriosInferior:
		entradaInf = 'El numero inferior al umbral %0.2f mas reciente obtenido es %0.2f (%s)' %(float(umbral), inferior['aleatorio'],inferior['hora'])
		menor.append(entradaInf)
	menorMostrar=menor[-1]


def umbral_superior(umbral):
	global mayorMostrar
	mayor=[]
	cliente = MongoClient()
	db = cliente['DBnumeros']
	AleatoriosDB = db['AletaoriosDB']
	aleatoriosSuperior = AleatoriosDB.find({'aleatorio':{'$gt':float(umbral)}})
	for superior in aleatoriosSuperior:
		entradaSup = 'El numero superior al umbral %0.2f mas reciente obtenido es %0.2f (%s)' %(float(umbral), superior['aleatorio'],superior['hora'])
		mayor.append(entradaSup)
	mayorMostrar=mayor[-1]	
	

@app.route('/', methods=['GET','POST'])
def index():
	if request.method == 'POST':
		boton=request.form['boton']
		if boton == 'Media':
			calcular_media()
			return render_template('web.html',media=mediaT)
		elif boton == 'Umbral':
			valorUmbral=request.form['UmbralText']
			umbral_superior(valorUmbral)
			umbral_inferior(valorUmbral)
			return render_template('web.html',umbrInf=menorMostrar,umbrSup=mayorMostrar)
		elif boton == 'Grafica':
			return redirect(url_grafica)
	else:
		return render_template('web.html')
		

if __name__ == '__main__':
	obtenerPeriodico = BackgroundScheduler()
	obtenerPeriodico.add_job(obtener_datos, 'interval', seconds=120)
	obtenerPeriodico.start()
	app.debug=True
	app.run(host='0.0.0.0')
