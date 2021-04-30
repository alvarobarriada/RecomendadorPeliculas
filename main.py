# Inicializa la aplicación
import os
import sys
from PyQt5 import QtMultimedia, QtWidgets, uic


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow,self).__init__()

        #Iniciamos la primera ventana
        uic.loadUi('pantalla_principal.ui',self)      
        qtRectangle = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())


        #Controladores de botones

        #Boton importar de Youtube
        #self.btnImportar.clicked.connect(self.insertarVideoYoutube)
        
        ## Botón siguiente (de 1ª a 2ª ventana)
        #self.btnSiguiente1.setEnabled(False)
        
    # Abrir cuadro de diálogo
    def openDialogBox(self):
        filename = QtWidgets.QFileDialog.getOpenFileName()
        return filename

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