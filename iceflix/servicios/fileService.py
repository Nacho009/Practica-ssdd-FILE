#!/usr/bin/env python3


from hashlib import sha256
import hashlib
from random import choice
import sys
import os
import logging
import time
import uuid
from main import *
#Importar catalogo 

import Ice

Ice.loadSlice("../Iceflix.ice")
import IceFlix

CHUNK_SIZE = 4096
servidorId=uuid.uuid4()

class FileServiceI (IceFlix.FileService):

     def __init__(self,main):
        self.authenticator= Main.getAuthenticator
        self.main=main
        # self.catalog= Catalog
        self.files={}
        
        cont=0
        for file in os.listdir("recursos"):
            self.files[cont]=file
            cont=cont+1

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

     def uploadFile(self, file_name, uploader, admin_token, current=None):
        
        if not self.authenticator.isAdmin(admin_token):
            raise IceFlix.Unauthorized()
                
        index = file_name.rfind("/")
        file_name = file_name[index + 1:]
        destination_file_name = "recursos/" + file_name

        try:
            with open(destination_file_name, 'wb') as out:
                while True:
                    chunk = uploader.receive(CHUNK_SIZE)
                    if not chunk:
                        break
                    out.write(chunk)
            uploader.close()

            with open(destination_file_name, 'rb') as file:
                contenido=file.read()
                id= hashlib.sha256(contenido).hexdigest()

            file.close()

            self.Catalog.mediaCatalog.newMedia(id,servidorId)

        except OSError: #Mirar este except
            raise IceFlix.TemporaryUnavaible
    
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

    def close(usertoken):
        return 0

class FileApp(Ice.Application):

    def __init__(self):
        super().__init__()
        self.servant = FileServiceI()
        self.proxy = None
        self.adapter = None
        self.mainProxy = None
        self.serviceId= servidorId

    def run(self, args):
        logging.info("Running File application")

        comm = self.communicator()
        self.adapter = comm.createObjectAdapter("FileService")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)

        self.mainProxy= comm.propertyToProxy("Main.Proxy")

        self.shutdownOnInterrupt()
        comm.waitForShutdown()
        self.mainProxy.newService(self.proxy,self.serviceId)

        for file in os.listdir("recursos"):
            self.Catalog.mediaCatalog.newMedia(sha256(file.encode()).hexdigest(),servidorId)

        while True:
            time.sleep(25.0)
            self.mainProxy.announce(self.proxy,self.serviceId)

if __name__ == "__main__":
    FileApp().main(sys.argv)
