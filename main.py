# Imports
import os
import sys
from PyQt5 import QtMultimedia, QtWidgets, uic

# Variables globales
RANKING_DEFAULT = 5

class MyWindow(QtWidgets.QMainWindow):
    
    def __init__(self):
        super(MyWindow,self).__init__()

        #Iniciamos la primera ventana
        uic.loadUi('Interface/main.ui',self)      

        #Boton recomendar
        self.btnRecomendar.clicked.connect(self.recomendar)
        
        ## Botón predecir
        self.btnPredecir.clicked.connect(self.predecir)
        
    
    def recomendar(self):
        pass
    
    
    def predecir(self):
        pass

  
#Método main de la aplicación
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())