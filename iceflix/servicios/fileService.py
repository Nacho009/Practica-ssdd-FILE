#!/usr/bin/env python3


from hashlib import sha256
import hashlib
import sys
import os
import logging
import time
import uuid
from os import path
import base64
from main import *
#import catalogo 

import Ice

Ice.loadSlice("../Iceflix.ice")
import IceFlix

CHUNK_SIZE = 4096
servidorId=uuid.uuid4()

class FileServiceI (IceFlix.FileService):

     def __init__(self,main):
        self.authenticator= Main.getAuthenticator()
        self.main=main
        self.catalog= Main.getCatalog
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

 
        idAdapter=str(uuid.uuid4())

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

            self.catalog.mediaCatalog.newMedia(id,servidorId)

        except OSError: #Mirar este except
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
     
     #PREGUNTAR PROFESOR
# # El servicio permite descargar un archivo a usuarios autenticados.
#      def downloadFile(self, file_id, user_token, current=None):
#         # Verificar si el archivo ya se está subiendo
#         if file_id in self.files:

#         # Verificar si el archivo se ha subido completamente
#             if len(self.files[file_id]) == os.path.getsize('files/' + file_id):
#                 # Crear un archivo en disco con el contenido del archivo subido
#                 with open('files/' + file_id, 'wb') as f:
#                     f.write(self.files[file_id])

                
#             else:
#                 del self.files[file_id]
#                 # Lanzar una excepción indicando que el archivo no se ha subido correctamente
#                 raise IceFlix.TemporaryUnavaible
#         else:
#             logging.info(f"Fichero ---> {file_id} No encontrado.")
        
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
        self.mainProxy = None
        self.serviceId= servidorId
        self.catalog=Main.getCatalog

    def run(self, args):
        logging.info("Running File application")

        broker = self.communicator()
        self.adapter = broker.createObjectAdapter("FileService","tcp")
        self.adapter.activate()

        self.servant.broker=broker
        self.proxy = self.adapter.addWithUUID(self.servant)

        self.mainProxy= broker.propertyToProxy("Main.Proxy")

        self.shutdownOnInterrupt()
        broker.waitForShutdown()
        self.mainProxy.newService(self.proxy,self.serviceId)

# El servicio notifica al catálogo de todos los archivos en su directorio inicial.
        for file in os.listdir("recursos"):
            self.catalog.mediaCatalog.newMedia(sha256(file.encode()).hexdigest(),servidorId)

        while True:
            time.sleep(25.0)
            self.mainProxy.announce(self.proxy,self.serviceId)

if __name__ == "__main__":
    FileApp().main(sys.argv)
