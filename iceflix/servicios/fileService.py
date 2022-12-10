#!/usr/bin/env python3


from hashlib import sha256
from random import choice
import sys
import os
import logging

import uuid
from main import * 
#Importar catalogo
import Ice

Ice.loadSlice("../Iceflix.ice")
import IceFlix


servidorId=uuid.uuid4()

class FileServiceI (IceFlix.FileService):

     def __init__(self):
        self.authenticator= Main.getAuthenticator
        # self.catalog= Catalog
        self.files={}
        
    #Comprueba si existe ese archivo en el directorio recursos.

     def exist(self, file_id, current=None):

            for file in os.listdir("recursos"):
                if file_id == sha256(file.encode()).hexdigest():
                    return True
            return False

     def openFile(self, file_id, user_token, current=None):

        path=self.files[file_id]

        if not self.authenticator.isAuthorized(user_token):
            raise IceFlix.Unauthorized()

        if not self.exist(file_id):
            raise IceFlix.WrongMediaId()
        else:

            file_handler= FileHandler(path)
            prx_handler=current.adapter.addWithUUID(file_handler)

            return IceFlix.FileServicePrx.uncheckedCast(prx_handler)
    
    
     def deleteFile(self, file_id, admin_token, current=None):
       
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

class FileHandler():

    def receive(self, size, user_token, current=None):
        if not self.authenticator.isAuthorized(user_token):
             raise IceFlix.Unauthorized()

    def close(user_token):
        return 0 

class FileApp(Ice.Application):

    def __init__(self):
        super().__init__()
        self.servant = FileServiceI()
        self.proxy = None
        self.adapter = None
        self.mainProxy = None
        self.serviceId= servidorId