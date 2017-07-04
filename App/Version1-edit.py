#!/usr/bin/env python
#-----------Imports
print "\nStarting, please wait...\n"
from Tkinter import *
print "Tkinter Loaded"
import numpy as np 				#Numpy, Libreria para trabajar con numeros n-dimensionales
print "Numpy Loaded"
import scipy						#Scipy, funciones para extender Numpy
import scipy.io as sio				#Scipy Input / Output para leer .mat
print "Scipy Loaded"
import matplotlib 				#MatPlotLib, Libreria para hacer graficos
matplotlib.use("TkAgg") 			#Opcion para empotrar graficos en ventanas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plot
from matplotlib import rc			#Sublibreria para mejoras en el texto y tipografias
print "Matplotlib Loaded"
import seabreeze					#Seabreeze, Libreria para manejo de dispositivos OceanOptics
seabreeze.use('pyseabreeze')		#Opcion para usar Seabreeze bajo libreria PyUSB
import seabreeze.spectrometers as sb
print "pySeabreeze Loaded"
#-----------End of Imports

#PARAMETROS DE MEDICION:
#Ingresar aqui:
int_time=	80000  			#Tiempo de integracion [microsegundos]
promedios=	5				#Cantidad de capturas por medicion
width=		8				#Ancho del suavizado (Boxcar Smoothing)

#DETECCION DEL ESPECTROMETRO:
#Se obtiene el listado de dispositivos OceanOptics:
devices = sb.list_devices() 
if len(devices)==0:
	print "\n\nERROR: Spectrometer not detected. Connect spectrometer and restart.\n\n"
else:
	#Se escoje como espectrometro el primero de la lista,
	#asumiendo que hay solo un aparato OceanOptics conectado al PC:
	spec = sb.Spectrometer(devices[0])
	#Notificacion
	print 'OceanOptics Spectrometer Model '+spec.model+' Serial number: ' + spec.serial_number + ' Loaded'
	#Guardar valores de longitud de onda (wavelengths) del aparato:
	x=spec.wavelengths()[0:3648]
	#Fijar el tiempo de integracion en el aparato: 
	spec.integration_time_micros(int_time)

#MODELOS DE ESTIMACION MS, SSR, SSH, AC

#Importar variables de los modelos:
#Coeficientes sin formato, escribir valor aqui:

ms_coef=14.9859557
ssr_coef=15.450357
ssh_coef=7.32951437
ac_coef=16.2624986989

#Modelos, en formato '.mat' en la misma carpeta que este codigo,
#escribir nombre de archivo aqui:
path='/home/pi/Desktop/Kiwis/'

nombre_archivo_ms='Modelo1415MS.mat'
nombre_archivo_ssr='Modelo1415SSR.mat'
nombre_archivo_ssh='Modelo1415SSH.mat'
nombre_archivo_ac='MODELO AC.mat'

#Aqui se rescata el nombre de la variable

nombre_matlab_ms=(sio.whosmat(path+nombre_archivo_ms))[0][0]
nombre_matlab_ssr=(sio.whosmat(path+nombre_archivo_ssr))[0][0]
nombre_matlab_ssh=(sio.whosmat(path+nombre_archivo_ssh))[0][0]
nombre_matlab_ac=(sio.whosmat(path+nombre_archivo_ac))[0][0]


ms_model=sio.loadmat(path+nombre_archivo_ms)[nombre_matlab_ms][0]
print 'Model from '+nombre_archivo_ms+', [Size: '+str(ms_model.size)+']. Loaded.'

ssr_model=sio.loadmat(path+nombre_archivo_ssr)[nombre_matlab_ssr][0]
print 'Model from '+nombre_archivo_ssr+', [Size: '+str(ssr_model.size)+']. Loaded.'

ssh_model=sio.loadmat(path+nombre_archivo_ssh)[nombre_matlab_ssh][0]
print 'Model from '+nombre_archivo_ssh+', [Size: '+str(ssh_model.size)+']. Loaded.'

ac_model=sio.loadmat(path+nombre_archivo_ac)[nombre_matlab_ac][0]
print 'Model from '+nombre_archivo_ac+', [Size: '+str(ac_model.size)+']. Loaded.'


#TODO Archivos de salida (Carpeta con txt Mediciones y Vectores de Estimaciones)



#CREACION DE LA VENTANA
#Definimos nuestra ventana principal
class Ppal:
	def __init__(self, master):	
		#frame = Frame(master)
		#frame.pack()		
		
		self.label_nombre_sesion = Label(master,text="Nombre de Sesion:").grid(row=0,column=0)
		
		self.entry_nombre_sesion = Entry(master).grid(row=1,column=0)
		#self.entry_nombre_sesion.insert(END, "mediciones-DDMMAA")
		
		self.boton_blanco = Button(master,text="Capturar Espectro Blanco", command=self.getwhite).grid(row=2,column=0)
		
		self.boton_negro = Button(master,text="Capturar Espectro Negro", command=self.getblack).grid(row=3,column=0)
				
		self.boton_medir = Button(master,text="Medir", command=self.button_measure).grid(row=4,column=0)
		
		self.label_ms = Label(master,text="MS:",font=("Helvetica",23)).grid(row=5,column=0)

		self.label_ssr = Label(master,text="SSR:",font=("Helvetica",23)).grid(row=6,column=0)

		self.label_ssh = Label(master,text="SSH:",font=("Helvetica",23)).grid(row=7,column=0)

		self.label_ac = Label(master,text="AC:",font=("Helvetica",23)).grid(row=8,column=0)

		self.boton_salir = Button(master,text="Salir",command=master.destroy).grid(row=9,column=0)

		self.figura = Figure(figsize=(8,5),dpi=72)
		self.grafico = self.figura.add_subplot(111)
		self.grafico.set_title('Espectro de Absorbancia')
		self.grafico.set_xlabel('Longitud de Onda ($\lambda$) [nm]')
		self.grafico.set_ylabel('Absorbancia [%]')
		self.grafico.axis([650,1300,0,1.5])
		self.telar = FigureCanvasTkAgg(self.figura)
		self.telar.get_tk_widget().grid(row=0,column=1,rowspan=9)

		self.i=0 #Contador de Mediciones
	
	#FUNCIONES PARA LOS BOTONES:
	
	def getwhite(self):
		self.whi=self.medir()
		print 'White Spectra Loaded. Size: '+str(self.whi.size)
		
	def getblack(self):
		self.bla=self.medir()
		print 'Black Spectra Loaded. Size: '+str(self.bla.size)
		
	def estimader(self,absor,model,coef):
		dec=2 #Cantidad de decimales de redondeo
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
		self.i=self.i+1				 	#Aumentar contador
		y=self.medir()					#Obtener mediciones
		absorbance=np.log10(self.whi/y)	#Calcular Absorbancia
		
		#Estimar MS, SSR, SSH & AC
		
		ms=self.estimader(absorbance,ms_model,ms_coef)
		ssr=self.estimader(absorbance,ssr_model,ssr_coef)
		ssh=self.estimader(absorbance,ssh_model,ssh_coef)
		ac=self.estimader(absorbance,ac_model,ac_coef)
		
		#Mostrar estimaciones
		self.label_ms.config(text="MS: "+str(ms))
		self.label_ssr.config(text="SSR: "+str(ssr))
		self.label_ssh.config(text="SSH: "+str(ssh))
		self.label_ac.config(text="AC: "+str(ac))
		print str(self.i)+')\tMS = '+str(ms)+'\tSSR = '+str(ssr)+'\tSSH = '+str(ssh)+'\tAC = '+str(ac)

		#TODO Guardar estimaciones y espectros capturados
		
		#Graficar:
		self.grafico.plot(x,absorbance)
		plot.axis([650,1300,0,1.5])
		plot.xlabel('Longitud de Onda ($\lambda$) [nm]')
		plot.ylabel('Absorbancia [%]')
		plot.grid(True)
		plot.title('Espectro de Absorbancia')
		plot.show()
		

root = Tk()
app = Ppal(root)
root.wm_title("SS y MS de Kiwis")
root.geometry("800x450")
root.mainloop()
