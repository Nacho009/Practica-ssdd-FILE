#!/usr/bin/env python3


from hashlib import sha256
import sys
import os
import logging
import time
import uuid
from os import path
from main import *


import Ice

Ice.loadSlice("../Iceflix.ice")
import IceFlix

CHUNK_SIZE = 4096
servidorId=uuid.uuid4()

#ENTREGA ONDINARIA P1

class FileServiceI (IceFlix.FileService):

     def __init__(self):
        self.authenticator= Main.getAuthenticator()
        self.catalog= Main.getCatalog()
        self.files={}
        
        for file in os.listdir("recursos"):
            self.files[sha256(file.encode()).hexdigest()]=file
            

#Comprueba si existe ese archivo en el directorio recursos.
     def exist(self, file_id, current=None):

            for file in os.listdir("recursos"):
                # El servicio calcula los “media id” utilizando el algoritmo especificado.
                if file_id == sha256(file.encode()).hexdigest():
                    return True
            return False
# El servicio permite abrir un archivo existente a un usuario válido.
     def openFile(self, file_id, user_token, current=None):
        path="recursos/"
        path+=self.files[file_id]

        if not self.authenticator.isAuthorized(user_token):
            raise IceFlix.Unauthorized()

        if not self.exist(file_id):
            raise IceFlix.WrongMediaId()
        else:
# El programa crea objetos de tipo FileHandler sólo cuando son necesarios, bajo demanda.
            file_handler= FileHandler(path)
            prx_handler=current.adapter.addWithUUID(file_handler)

            return IceFlix.FileServicePrx.uncheckedCast(prx_handler)


# El servicio permite que el administrador pueda subir un archivo.
     def uploadFile(self, file_name, uploader, admin_token, current=None):
        
        if not self.authenticator.isAdmin(admin_token):
            raise IceFlix.Unauthorized()
                
        
        index = file_name.rfind("/")
        file_name = file_name[index + 1:]
        file_id=sha256(file_name.encode()).hexdigest()
        destination_file_name = "recursos/" + file_name

        bytes=0

        try:
            with open(destination_file_name, 'wb') as out:
                while True:
                    chunk = uploader.receive(CHUNK_SIZE)
                    if not chunk:
                        break
                    out.write(chunk)
                    bytes+=chunk

            uploader.close()

            with open(destination_file_name, 'rb') as file:
                contenido=file.read()
                id= sha256(contenido).hexdigest()

            file.close()

            if os.path.getsize('recursos/' + self.files[file_id])==bytes:
                self.catalog.mediaCatalog.newMedia(id,servidorId)
            else:
                logging.info(f"Fichero ---> {file_id} no se ha descargado completo, por lo que se descarta.")


        except OSError: 
            raise IceFlix.TemporaryUnavaible

# El servicio permite eliminar un archivo al administrador.
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
        self.catalog.MediaCatalog.removedMedia(file_id, servidorId)
        
class FileHandler(IceFlix.FileHandler):

    def __init__(self,file_path):
        super().__init__()

        self.authenticator= Main.getAuthenticator()

        if not path.isfile(file_path):
             raise IceFlix.WrongMediaId()

        self.destination_file = file_path
        self.file = open(self.destination_file, 'rb')  # pylint: disable=consider-using-with

    def receive(self, size, user_token, current=None):

        if not self.authenticator.isAuthorized(user_token):
             raise IceFlix.Unauthorized()

        chunk = self.file.read(size)
        return chunk

        

    def close(self, user_token, current=None):

         if not self.authenticator.isAuthorized(user_token):
             raise IceFlix.Unauthorized()

         self.file.close()
         current.adapter.remove(current.id)


class FileApp(Ice.Application):

    def __init__(self):
        super().__init__()
        self.servant = FileServiceI()
        self.proxy = None
        self.adapter = None
        self.mainPrx = None
        self.serviceId= servidorId
        self.catalog=Main.getCatalog

    def run(self, args):
        logging.info("Running File application")

        broker = self.communicator()
        self.adapter = broker.createObjectAdapter("FileService","tcp")
        self.adapter.activate()

        self.proxy = self.adapter.addWithUUID(self.servant)

        self.mainPrx= broker.propertyToProxy("Main.Proxy")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        self.mainPrx.newService(self.proxy,self.serviceId)

# El servicio notifica al catálogo de todos los archivos en su directorio inicial.
        for file in os.listdir("recursos"):
            self.catalog.mediaCatalog.newMedia(sha256(file.encode()).hexdigest(),servidorId)
            
        # while True:
        #     time.sleep(25.0)
        #     self.mainPrx.announce(self.proxy,self.serviceId)

if __name__ == "__main__":
    FileApp().main(sys.argv)
