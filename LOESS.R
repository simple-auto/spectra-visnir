###CARGA TXT TRANSMITANCIAS####

print("Ingrese directorio de trabajo")
directorio<-readline()

setwd(directorio)
archivo <-readline()

###LOESS####
datos <- read.table(archivo,sep="\t",header = TRUE)
datos2 <- data.frame()
for(frutos in 2:ncol(datos)){
  
  ajuste<-loess.smooth(datos$wvl,datos[,frutos],span = 0.1,degree = 2,family = "gaussian", evaluation = 3648)
  ajuste$x<-round(ajuste$x,digits = 0)
  suavizado<-vector()
  for (i in 1:901) {
    z<-i+199
    pos<-which(ajuste$x==z)
    suavizado[z-199]<-mean(ajuste$y[pos])
  }
  
  if(frutos==2)
  {
    datos2<-cbind(c(200:1100),suavizado,deparse.level = 0)
  } 
  else   {
    datos2<-cbind(datos2,suavizado,deparse.level = 0)
    colnames(datos2)<-c(colnames(datos[1]),colnames(datos[2:frutos]))
  }
}

rownames(datos2) <- datos2[,1]
datos2 <- datos2[,2:ncol(datos2)]

print ("Proceso Terminado")

###EXPORTAR MATRIZ####
library(xlsx)
print("Nombre de archivo de salida: archivo.xlsx")
archivoexcel <-readline()

###SALIDA EXCEL####
write.xlsx(datos2, file = archivoexcel, col.names = TRUE, sheetName = archivoexcel)

print("Archivo Exportado")