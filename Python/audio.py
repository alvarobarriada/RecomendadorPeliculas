
from pygame import mixer
import time

def musica_ascensor(a):
    mixer.init()
    mixer.music.load(r'Database/musica.mp3')
    mixer.music.set_volume(1.0)
    #Se reproduce en bucle
    mixer.music.play(loops = -1)
    if (a == True):
        #Para que empiece
        time.sleep(5)
    else: 
        #Para parar el bucle
        mixer.music.stop()

