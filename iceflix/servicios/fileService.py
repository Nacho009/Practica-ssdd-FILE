

from hashlib import sha256
import os
import Ice

Ice.loadSlice("../Iceflix.ice")
import IceFlix




#class FileHandlerI (IceFlix.FileHandler):

class FileServiceI (IceFlix.FileService):


    #Comprueba si existe ese archivo en el directorio recursos.

     def existe(self, file_id, current=None):

            for file in os.listdir("recursos"):
                if file_id == sha256(file.encode()).hexdigest():
                    return True
            return False

     
    #CODIGO openFile que se puso en clase
    
    # def openFile(self, file_id, user_token, current):
    #     path=self.files[file_id]
    #     fh=FileHandler(path)
    #     prx=current.adapter.addWithUUID(fh)
    #     return IceFlix.FileServicePrx.uncheckedCast(fh)
    # Ice.Current()