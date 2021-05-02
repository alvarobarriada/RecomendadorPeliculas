# Inicializa la aplicación
import os
import sys
from PyQt5 import QtMultimedia, QtWidgets, uic


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow,self).__init__()

        #Iniciamos la primera ventana
        uic.loadUi('main.ui',self)      
        """qtRectangle = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())"""


        #Boton recomendar
        self.btnRecomendar.clicked.connect(self.recomendar)
        
        ## Botón predecir
        self.btnPredecir.clicked.connect(self.predecir)
        
    # Abrir cuadro de diálogo
    def openDialogBox(self):
        filename = QtWidgets.QFileDialog.getOpenFileName()
        return filename
    
    def recomendar(self):
        pass
    
    def predecir(self):
        pass

    #------------ Funciones Botones Segunda Ventana ------------#
    """
    #Cambiar a segunda pantalla
    def cambiarSegundaVentana(self):
        #Cargamos la segunda ventana
        uic.loadUi('segundapantalla.ui', self)
        qtRectangle = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
    """
    
    #Guarda los cambios en un txt
    def guardarCambios(self):
        global texto
        texto = self.txt_transcripcion.toPlainText()
        filename = self.txt_filename.toPlainText()
        save(texto, filename)

#Método main de la aplicación
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())