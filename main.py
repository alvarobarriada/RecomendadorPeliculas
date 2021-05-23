# Imports
from Python import funciones, audio
from PyQt5 import QtWidgets, uic
from PyQt5.Qt import QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import os
import sqlite3
import sys
  
# Conexión con la base de datos SQLite
connection = sqlite3.connect(r'Database/Movielens.db')

# Se crea un cursor para ejecutar las órdenes SQL
cursor = connection.cursor()

# Número por defecto de items del ranking
RANKING_DEFAULT = 5
class MyWindow(QtWidgets.QMainWindow):
    
    def __init__(self):
        super(MyWindow,self).__init__()

        #Iniciamos la primera ventana
        uic.loadUi('Interface/main.ui',self)
        
        self.estrella.setHidden(True)
        self.estrella.setHidden(True)
        self.estrella_2.setHidden(True)
        self.estrella_3.setHidden(True)
        self.estrella_4.setHidden(True)
        self.estrella_5.setHidden(True)
        self.error_radio.setHidden(True)

        #Boton recomendar
        self.btnRecomendar.clicked.connect(self.recomendar)
        
        ## Botón predecir
        self.btnPredecir.clicked.connect(self.predecir)

    def recomendar(self):
        # resetear tabla
        self.tabla.setRowCount(0)
        
        # Recogemos valores de userId y número de elementos a mostrar
        userId = self.userarriba.toPlainText()
        numero = self.items.toPlainText()
        if numero == '':
            numero = RANKING_DEFAULT
        # Recomendación con número de vecinos
        if self.radioPatio.isChecked():
            audio.musica_ascensor(True)

            print("Has elegido número de vecinos")
            self.error_radio.setHidden(True)
            
            if int(self.vecinos.toPlainText()) != 5:
                vecinos = int(self.vecinos.toPlainText())
            else:
                vecinos = RANKING_DEFAULT

            # Si recomendamos con vecinos, umbral es None
            recomendacion = funciones.predecir_recomendacion(int(userId), int(numero), None, int(vecinos))
            
            if (len(recomendacion)-1 != 0 ):
            # Mostramos valores en la tabla
                self.resultadosTabla(int(numero), recomendacion)
                audio.musica_ascensor(False)
            else:
                self.pie.setText('No se han encontrado recomendaciones para las condiciones indicas.')
                self.pie.setHidden(False)
                
        
        # Recomendación con umbral de similitud
        elif self.radioUmbral.isChecked():
            audio.musica_ascensor(True)

            print("Has elegido umbral de similitud")
            self.error_radio.setHidden(True)

            umbral = self.umbral.toPlainText()

            # Si recomendamos con umbral, vecinos es None
            recomendacion = funciones.predecir_recomendacion(int(userId), int(numero), float(umbral), None)
            
            # Mostramos valores en la tabla
            if (len(recomendacion)-1 != 0 ):
                # Mostramos valores en la tabla
                self.resultadosTabla(int(numero), recomendacion)
                audio.musica_ascensor(False)
            else:
                self.pie.setText('No se han encontrado recomendaciones para las condiciones indicas.')
                self.pie.setHidden(False)
        # Prevención de errores    
        else:
            print("Por favor, seleccione una de las opcionesSeleccione una opción")
            self.error_radio.setHidden(False)


    def insertar_foto(self, movieId):
        path = 'Database/img/' + str(movieId) + '.jpg'
        pixmap = QPixmap(path)
        self.img_pelicula.setPixmap(pixmap)
        
    def predecir(self):
        self.estrella.setHidden(True)
        self.estrella.setHidden(True)
        self.estrella_2.setHidden(True)
        self.estrella_3.setHidden(True)
        self.estrella_4.setHidden(True)
        self.estrella_5.setHidden(True)
        usuario = self.userabajo.toPlainText()
        pel = self.pelicula.toPlainText()
        peli = pel.replace('(', '')
        pelicula = peli.replace(')', '')
        pred = funciones.prediccion(pelicula, int(usuario))
        nombre = funciones.fuzzy(pelicula)
        if (nombre != None):
            name = nombre[0][0]
            self.pelicula.setText(name)
            movieId = nombre[0][1]

            # Comprobación antes de insertar foto de que el archivo existe en la base de datos
            ruta_foto = 'Database/img/' + str(movieId) + '.jpg'
            if os.path.isfile(ruta_foto):
                self.insertar_foto(movieId)
            else:
                funciones.download_image(movieId)
                self.insertar_foto(movieId)
                
            if (pred == 1e-8):
                info = 'Ya la ha valorado'
                self.prediccion_2.setAlignment(Qt.AlignCenter)
                self.prediccion_2.setText(info)

            else:
                stars = int(pred)
                format_float = "{:.2f}".format(pred)
                info = str(format_float)
                self.prediccion_2.setText(info)
                if(stars == 1):
                    self.prediccion_2.setAlignment(Qt.AlignCenter)
                    self.estrella_3.setHidden(False)
                    
                elif(stars == 2):
                    self.prediccion_2.setAlignment(Qt.AlignCenter)
                    self.estrella_2.setHidden(False)
                    self.estrella_3.setHidden(False)
                    format_float = "{:.2f}".format(pred)
                    info = str(format_float)
                    self.prediccion_2.setText(info)
                elif (stars == 3):
                    self.prediccion_2.setAlignment(Qt.AlignCenter)
                    self.estrella.setHidden(False)
                    self.estrella_2.setHidden(False)
                    self.estrella_3.setHidden(False)
                    format_float = "{:.2f}".format(pred)
                    info = str(format_float)
                    self.prediccion_2.setText(info)
                elif (stars == 4):
                    self.prediccion_2.setAlignment(Qt.AlignLeft)
                    self.estrella_5.setHidden(False)
                    self.estrella_4.setHidden(False)
                    self.estrella_2.setHidden(False)
                    self.estrella_3.setHidden(False)
                    format_float = "{:.2f}".format(pred)
                    info = str(format_float)
                    self.prediccion_2.setText(info)
                elif(stars == 0):
                    self.prediccion_2.setAlignment(Qt.AlignCenter)
                    format_float = "{:.2f}".format(pred)
                    info = str(format_float)
                    self.prediccion_2.setText(info)
        else:
            info = 'Película no encontrada'
            self.prediccion_2.setAlignment(Qt.AlignCenter)
            self.prediccion_2.setText(info)
            path_error = 'Database/img/error.png'
            pixmap = QPixmap(path_error)
            self.img_pelicula.setPixmap(pixmap)
            
    def resultadosTabla(self, numero, recomendaciones):
        # para ocupar toda la tabla
        self.tabla.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        
        # resetear tabla
        self.tabla.setRowCount(0)

        self.tabla.setRowCount(numero)
        self.tabla.setColumnCount(2)
        for i, text in enumerate(recomendaciones):
            pred = text[1]
            format_float = "{:.2f}".format(pred)
            info = str(format_float)
            self.tabla.setItem(i, 0, QTableWidgetItem(text[0]))
            self.tabla.setItem(i, 1, QTableWidgetItem(info))

#Método main de la aplicación
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())