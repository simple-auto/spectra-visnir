#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Vis = Visible
#NIR = Near Infra-Red

#-----------Imports
import os
print "Spectra Vis/NIR v17.04\n\nIniciando Componentes...\n"
from Tkinter import *
import ttk
print "Tkinter Cargado"
import numpy as np 				#Numpy, Libreria para trabajar con numeros n-dimensionales
print "Numpy Cargado"
import scipy						#Scipy, funciones para extender Numpy
import scipy.io as sio				#Scipy Input / Output para leer .mat
print "Scipy Cargado"
import matplotlib 				#MatPlotLib, Libreria para hacer graficos
matplotlib.use("TkAgg") 			#Opcion para empotrar graficos en ventanas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import rc			#Sublibreria para mejoras en el texto y tipografias
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
plt.ion()
print "Matplotlib Cargado"
#import pylab
#pylab.ion()
#print "Pylab Loaded"
import seabreeze			#Seabreeze, Libreria para manejo de dispositivos OceanOptics
seabreeze.use('pyseabreeze')		#Opcion para usar Seabreeze bajo libreria PyUSB
import seabreeze.spectrometers as sb
print "pySeabreeze Cargado"
#-----------End of Imports

#CONFIGURACION DEL ESPECTROMETRO:
#Parametros de medicion:

int_time=	700000  		#Tiempo de integracion [microsegundos]
promedios=	2			#Cantidad de capturas por medicion
width=		3			#Ancho del suavizado (Boxcar Smoothing)

#DETECCION DEL ESPECTROMETRO
#Se obtiene el listado de dispositivos OceanOptics:
devices = sb.list_devices() 
if len(devices)==0:
	print "\n\nERROR: Espectrometro no detectado, reconectar dispositivo y reiniciar app.\n\n"
else:
	#Se escoje como espectrometro el primero de la lista,
	#asumiendo que hay solo un aparato OceanOptics conectado al PC:
	spec = sb.Spectrometer(devices[0])
	#Notificacion
	print '\nEspectrometro ' + spec.serial_number + ' Dispositivo Listo'
	#Guardar valores de longitud de onda (wavelengths) del aparato:
	x=spec.wavelengths()[0:3648]
	#Fijar el tiempo de integracion en el aparato: 
	spec.integration_time_micros(int_time)

#FILE I/O
input_path='/home/pi/Desktop/spectra-visnir/App/'
output_path='/home/pi/Desktop/spectra-visnir/Resultados/'

#MODELO DE ESTIMACION PLS MANZANAS
#Coeficiente
pls_manzanas_coef=1.57331
nombre_archivo_pls_manzanas='mod_pls_manzanas.mat'
nombre_matlab_pls_manzanas=(sio.whosmat(input_path+nombre_archivo_pls_manzanas))[0][0]
pls_manzanas_model=sio.loadmat(input_path+nombre_archivo_pls_manzanas)[nombre_matlab_pls_manzanas][0]

#CREACION DE LA VENTANA

#Definimos nuestra ventana principal
class Ppal:
	def __init__(self, master):	
	
		frame = Frame(master)
		frame.grid(column=0)		

		self.label_titulo = Label(frame, text = "Spectra Vis/NIR",font=("Helvetica",20))
		self.label_titulo.grid(row=0,columnspan=3)

		self.separador = ttk.Separator(frame,orient=HORIZONTAL)
		self.separador.grid(row=1,columnspan=3,sticky="ew")

		self.label_nombre_sesion = Label(frame,text="Nombre de Sesion:")
		self.label_nombre_sesion.grid(column=0)
		
		self.entry_nombre_sesion = Entry(frame)
		self.entry_nombre_sesion.insert(END, "nombre_carpeta")
		self.entry_nombre_sesion.grid(column=0)
		self.sesion_iniciada=False

		self.boton_crear_sesion = Button(frame,text="Crear Sesion", command=self.create_new_session)
		self.boton_crear_sesion.grid(column=0)
		
		self.boton_blanco = Button(frame,text="Guardar Ref. Maxima", command=self.getwhite)
		self.boton_blanco.grid(column=0)
		
		#self.boton_negro = Button(frame,text="Capturar Espectro Negro", command=self.getblack)
		#self.boton_negro.grid(column=0)
		
		self.boton_medir = Button(frame,text="Medir", command=self.button_measure,state=DISABLED,font=("Helvetica",16))
		#self.bind('m',self.button_measure)		
		self.boton_medir.grid(column=0)
		
		self.booleano_ms = IntVar()
		self.booleano_ssr = IntVar()
		self.booleano_ssh = IntVar()
		self.booleano_ac = IntVar()

		#self.check_and_label_ms = Checkbutton(frame,text="MS:",font=("Helvetica",20),variable=self.booleano_ms)
		#self.check_and_label_ms.grid(column=0)
		#self.check_and_label_ssr = Checkbutton(frame,text="SS_R:",font=("Helvetica",20),variable=self.booleano_ssr)
		#self.check_and_label_ssr.grid(column=0)
		#self.check_and_label_ssh = Checkbutton(frame,text="SS_H:",font=("Helvetica",20),variable=self.booleano_ssh)
		#self.check_and_label_ssh.grid(column=0)
		#self.check_and_label_ac = Checkbutton(frame,text="AC:",font=("Helvetica",20),variable=self.booleano_ac)
		#self.check_and_label_ac.grid(column=0)

		self.boton_borrar_ultimo = Button(frame,text="Borrar Ultimo",command=self.erase_last,state=DISABLED)
		self.boton_borrar_ultimo.grid(column=0)

		self.boton_salir = Button(frame,text="Salir",command=master.destroy)
		self.boton_salir.grid(column=0)
	
		self.figura = Figure(figsize=(7.5,5.3))
		self.grafico = self.figura.add_subplot(111)
		self.grafico.set_title('Espectro de Transmitancia')
		self.grafico.set_xlabel('Longitud de Onda ($\lambda$) [nm]')
		self.grafico.set_ylabel('Intensidad [counts]')
		self.grafico.axis([400,1100,0,10000])
		self.grafico.grid(True)

		self.telar = FigureCanvasTkAgg(self.figura, master=frame)
		self.telar.get_tk_widget().grid(row=2,column=1,rowspan=11,columnspan=2)

		self.ejes=self.figura.gca()

		self.separador2 = ttk.Separator(frame,orient=HORIZONTAL)
		self.separador2.grid(row=14,columnspan=3,sticky="ew")

		self.recuadro_mensaje = Text(frame,height=4,width=111)
		self.recuadro_mensaje.grid(row=15, column=0,columnspan=2)
		self.deslizador_mensaje = Scrollbar(frame)
		self.recuadro_mensaje.config(yscrollcommand = self.deslizador_mensaje.set)
		self.deslizador_mensaje.config(command = self.recuadro_mensaje.yview)
		self.deslizador_mensaje.grid(row=15,column=2,sticky="nsw")

		self.desplegar_mensaje("Bienvenido")
		self.desplegar_mensaje("Spectra Vis/NIR v17.04 - Laboratorio de Poscosecha UC")

		self.i=0 #Contador de Mediciones
		self.w=0 #Contador de Espectros Blancos

	#FUNCIONES PARA LOS BOTONES:

	def desplegar_mensaje(self,texto_mensaje):
		self.recuadro_mensaje.insert(END,texto_mensaje+"\n")
		self.recuadro_mensaje.see('end')
	
	def create_new_session(self):
		self.nombre_sesion=self.entry_nombre_sesion.get()	#Recoger el titulo entregado por el usuario
		#TODO Comprobar que el texto ingresado se puede usar como titulo

		if not os.path.exists(output_path+self.nombre_sesion):
			#Crear la carpeta:
			os.mkdir(output_path+self.nombre_sesion)

			#Botones:
			self.sesion_iniciada=True
			self.boton_crear_sesion.config(text="Sesion Creada",state=DISABLED)
			self.entry_nombre_sesion.config(state=DISABLED)

			#Crear archivo de estimaciones y guardar eje x:
			self.estimaciones_sesion=open(output_path+self.nombre_sesion+"/estimaciones.txt","a")
			self.estimaciones_sesion.write("no.\tMS\tSSR\tSSH\tAC\n")
			np.savetxt(output_path+self.nombre_sesion+"/wvl.txt",x)

			#Listo:
			self.recuadro_mensaje.delete(2.0,END)
			self.desplegar_mensaje("\nSesion Creada. Archivos se guardaran en "+output_path+self.nombre_sesion)
			self.boton_salir.config(command=self.cerrar_sesion,text="Cerrar Sesion")
		else:
			self.desplegar_mensaje("Sesion no creada (Nombre repetido o no valido)")

	def getwhite(self):
		self.whi=self.medir()
		self.boton_medir.config(state=NORMAL)
		self.w=self.w+1
		self.desplegar_mensaje("Referencia Blanco no."+str(self.w)+" cargado")
		if self.sesion_iniciada:
			#Guardar espectro blanco en la sesion
			np.savetxt(output_path+self.nombre_sesion+"/blanco_"+str(self.w),self.whi)
			
	def getblack(self):
		self.bla=self.medir()
		print 'Black Spectra Loaded. Size: '+str(self.bla.size)
		
	def estimader(self,absor,model,coef):
		dec=5 #Cantidad de decimales de redondeo
		return round(np.dot(model,absor)+coef, dec)
		
	def medir(self): #Usa las variables 'promedios' y 'width' definidas al principio
		#Tomar 'promedios' mediciones promediadas:
		y=spec.intensities()[0:3648]
		for p in range(promedios-1):
			y=(y+spec.intensities()[0:3648])/2
		#Aplicar boxcar smoothing:
		y=np.convolve(y, np.ones((width,))/width, mode='same')
		#Retornar resultado:
		return y
		
	def button_measure(self):
		y=self.medir()					#Obtener mediciones
		self.i=self.i+1				 	#Aumentar contador

                #Normalizar Potencia (Eliminar componente continua)
			#TODO Definir el metodo de normalizacion

                #Calcular Transmitancia
		
		#absorbance=np.log10(self.whi/y)	                #Calcular Absorbancia
		transmitance=np.true_divide(y/self.whi)		#Calcular Transmitancia
		
			
		#Graficar
		if True: #Escoger: True = Grafica solo el ultimo espectro, False = Grafica todos juntos
			#Reiniciar Grafico
			self.grafico.cla()		
			self.grafico.set_title('Espectro de Intensidad')
			self.grafico.set_xlabel('Longitud de Onda ($\lambda$) [nm]')
			#self.grafico.set_ylabel('Intensidad [counts]')
			self.grafico.set_ylabel('Ti [%]')
			self.grafico.axis([400,1100,0,10000])
			self.grafico.grid(True)

		#Dibujar Curva
		self.grafico.plot(x,transmitance)
		self.telar.draw()
		
		###---PREPROCESOS PLS---###
		
		#DOWNSAMPLING
		#TODO (DONE) bajar la resolucion a 1 wavelegth, i.e., x=(200,201,202,203,...,1100)
		
		wv_int=np.asarray(x,dtype=int)
		values=np.asarray(transmitance)
		#plt.figure()
		#plt.plot(wv,values)
		#plt.show()

		# Down-Samplear considerando el valor promedio
		Prom=np.asarray([0])
		Prom[0]=values[0]
		j=1
		for i in range(1,wv_int.size):
		    if wv_int[i]==wv_int[i-1]:
			Prom[-1]=np.add(Prom[-1]*j,values[i])/(j+1)
			j=j+1
		    else:
			j=1
			Prom=np.append(Prom,values[i])
		wv_int=np.unique(wv_int)

		
		#Regresion LOESS
		#TODO implementar funcion LOESS de R
		
		#Aplicar PLS
		#TODO (producto punto del output de loess por modelo pls)+coef_pls
		
		
		#Decision
		#TODO signo del resultado
		
		
		#Desplegar el mensaje
		#TODO cambiar label
		
		
		#Estimar y mostrar resultados de MS, SSR, SSH & AC (Solo seleccionados)

		#if self.booleano_ms.get()==1:
			#ms=self.estimader(absorbance,ms_model,ms_coef)
			#self.check_and_label_ms.config(text="MS: "+str(ms))		
		#else:
			#ms=-1
			#self.check_and_label_ms.config(text="MS off ")		

		#if self.booleano_ssr.get()==1:		
			#ssr=self.estimader(absorbance,ssr_model,ssr_coef)
			#self.check_and_label_ssr.config(text="SSR: "+str(ssr))
		#else:
			#ssr=-1
			#self.check_and_label_ssr.config(text="SSR off ")		

		#if self.booleano_ssh.get()==1:
			#ssh=self.estimader(absorbance,ssh_model,ssh_coef)
			#self.check_and_label_ssh.config(text="SSH: "+str(ssh))
		#else:
			#ssh=-1
			#self.check_and_label_ssh.config(text="SSH off ")		

		#if self.booleano_ac.get()==1:
			#ac=self.estimader(absorbance,ac_model,ac_coef)
			#self.check_and_label_ac.config(text="AC: "+str(ac))		
		#else:
			#ac=-1
			#self.check_and_label_ac.config(text="AC off ")		
		
		if self.sesion_iniciada==True:
			#Guardar mediciones	
			np.savetxt(output_path+self.nombre_sesion+"/espectro_"+str(self.i),y)
			
			#Descomentar linea siguiente para guardar espectro de absorbancia:			
			#np.savetxt(output_path+self.nombre_sesion+"/absorbancia-"+str(self.i),absorbance)

			#Guardar estimaciones
			#self.estimaciones_sesion.write(str(self.i)+"\t"+str(ms)+"\t"+str(ssr)+"\t"+str(ssh)+"\t"+str(ac)+"\n")
			#self.desplegar_mensaje(str(self.i)+')\tMS = '+str(ms)+'\tSSR = '+str(ssr)+'\tSSH = '+str(ssh)+'\tAC = '+str(ac))

		self.desplegar_mensaje("Medicion no."+str(self.i)+" realizada")
		#Activar Boton Borrar Ultimo
		self.boton_borrar_ultimo.config(state=NORMAL)

	def erase_last(self):
		#TODO Borrar archivos 
		#(por ahora se baja el contador y se sobreescriben en la siguiente medicion)		
		self.i=self.i-1
		
		#TODO Borrar estimaciones:
		#self.estimaciones_sesion
		#print str(self.i)+')\tMS = '+str(ms)+'\tSSR = '+str(ssr)+'\tSSH = '+str(ssh)+'\tAC = '+str(ac)

		self.desplegar_mensaje("Medicion no."+str(self.i+1)+" Borrada.")
		self.boton_borrar_ultimo.config(state=DISABLED)

		#Reiniciar Grafico:
		self.grafico.cla()		
		self.grafico.set_title('Espectro de Intensidad')
		self.grafico.set_xlabel('Longitud de Onda ($\lambda$) [nm]')
		self.grafico.set_ylabel('Intensidad [counts]')
		self.grafico.axis([400,1100,0,10000])
		self.grafico.grid(True)
		self.telar.draw()
		
	def cerrar_sesion(self):
		self.desplegar_mensaje("Sesion Finalizada")

		#Guardar Log (Texto inferior de la ventana) en un archivo
		log=open(output_path+self.nombre_sesion+"/registro.txt","w")
		log.write(self.recuadro_mensaje.get(2.0,END))
		log.close()

		#Cerrar documento de estimaciones
		self.estimaciones_sesion.close();

		#Restituir botones de la ventana:		
		self.sesion_iniciada=False
		self.boton_crear_sesion.config(state=NORMAL,text="Crear Sesion")
		
		self.entry_nombre_sesion.config(state=NORMAL)
		self.boton_salir.config(command=root.destroy,text="Salir")


#######################
#EJECUTAR VENTANA:
#######################

root = Tk()
root.title("Spectra Vis/NIR 17.04 - Poscosecha UC")
app = Ppal(root)
root.attributes('-fullscreen',False)
root.mainloop()
