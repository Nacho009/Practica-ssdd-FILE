#!/usr/bin/env python3


from hashlib import sha256
import sys
import os
import logging
import uuid

import Ice

Ice.loadSlice("../Iceflix.ice")
import IceFlix


servidorId=uuid.uuid4() # cambiar

class FileServiceI (IceFlix.FileService):

    #Comprueba si existe ese archivo en el directorio recursos.

     def exist(self, file_id, current=None):

            for file in os.listdir("recursos"):
                if file_id == sha256(file.encode()).hexdigest():
                    return True
            return False

    
    # ELIMINA UN FICHERO

     def deleteFile(self, file_id, admin_token, current=None):
        """Borra un vídeo del directorio resources"""
       
        if not self.authenticator.isAdmin(admin_token):
            raise IceFlix.Unauthorized()

        if not self.exist(file_id):
            raise IceFlix.WrongMediaId(file_id)

        else:
            
            for file in os.listdir("recursos"):
                if file_id == sha256(file.encode()).hexdigest():
                    os.remove("recursos/" + file)
                    break

        logging.info(f"Fichero ---> {file_id} eliminado.")
        self.Catalog.MediaCatalog.removedMedia(file_id, servidorId)

#CODIGO openFile que se puso en clase
    
    # def openFile(self, file_id, user_token, current):
    #     path=self.files[file_id]
    #     fh=FileHandler(path)
    #     prx=current.adapter.addWithUUID(fh)
    #     return IceFlix.FileServicePrx.uncheckedCast(fh)
    # Ice.Current()