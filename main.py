# Imports
import sqlite3
import sys
from PyQt5 import QtWidgets, uic
  
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

        #Boton recomendar
        self.btnRecomendar.clicked.connect(self.recomendar)
        
        ## Botón predecir
        self.btnPredecir.clicked.connect(self.predecir)
        
    
    def recomendar(self):

        # 1.- Cogemos la información del usuario
        usuario = self.userarriba.toPlainText()
        sql = 'SELECT * FROM ratings WHERE userID = '
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

    
    
    def predecir(self):
        pass

  
#Método main de la aplicación
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())