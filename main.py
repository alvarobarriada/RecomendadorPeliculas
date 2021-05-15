# Imports
from PyQt5.QtGui import QPixmap
from Python import funciones
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
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

        #Boton recomendar
        self.btnRecomendar.clicked.connect(self.recomendar)
        
        ## Botón predecir
        self.btnPredecir.clicked.connect(self.predecir)
        
    
    def recomendar(self):

        # 1.- Cogemos la información del usuario
        usuario = self.userarriba.toPlainText()
        sql = 'SELECT * FROM ratings WHERE userId = '
        query = sql + usuario
        print(query)
        cursor.execute(query)
        
        ## Imprimimos resultados
        result = cursor.fetchall()
        for x in result:
            print(x)

        # 2.- Cogemos el número de items a seleccionar
        if self.items.toPlainText() == "":
            num = RANKING_DEFAULT
        else:
            num = self.items.toPlainText()

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
            funciones.download_image(movieId)
            self.insertar_foto(movieId)

            if (pred == 1e-8):
                info = 'Ya la ha valorado'
                self.prediccion_2.setAlignment(Qt.AlignCenter)
                self.prediccion_2.setText(info)

            else:
                stars = int(pred)
                if(stars == 1):
                    self.prediccion_2.setAlignment(Qt.AlignCenter)
                    self.estrella_3.setHidden(False)
                elif(stars == 2):
                    self.prediccion_2.setAlignment(Qt.AlignCenter)
                    self.estrella_2.setHidden(False)
                    self.estrella_3.setHidden(False)
                elif (stars == 3):
                    self.prediccion_2.setAlignment(Qt.AlignCenter)
                    self.estrella.setHidden(False)
                    self.estrella_2.setHidden(False)
                    self.estrella_3.setHidden(False)
                elif (stars == 4):
                    self.estrella_5.setHidden(False)
                    self.estrella_4.setHidden(False)
                    self.estrella_2.setHidden(False)
                    self.estrella_3.setHidden(False)
                elif(stars == 0):
                    self.prediccion_2.setAlignment(Qt.AlignCenter)
                format_float = "{:.2f}".format(pred)
                info = str(format_float)
                #self.prediccion_2.setAlignment(Qt.AlignCenter)
                self.prediccion_2.setText(info)
        else:
            info = 'Pelicula no encontrada'
            self.prediccion_2.setAlignment(Qt.AlignCenter)
            self.prediccion_2.setText(info)
            



        
#Método main de la aplicación
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())