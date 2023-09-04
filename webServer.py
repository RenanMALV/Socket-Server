#import socket module
from socket import *
import sys # In order to terminate the program
import os # get file details
import time # to send time in response header lines
import signal # for manually closing the socket
from urllib.parse import unquote # for decoding url coded to UTF-8

#Prepare a sever socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverAddr = 'localhost'
serverPort = 80
serverSocket.bind((serverAddr, serverPort))
serverSocket.listen(5)
serverSocket.settimeout(5.0)
print('Servidor inicializado em ', serverSocket.getsockname())

def closeServer(sigNumber, _):
    print("Encerrando servidor...", "Sinal:", signal.Signals(sigNumber).name)
    serverSocket.close()
    sys.exit()#Terminate the program after sending the corresponding data

signal.signal(signal.SIGINT, closeServer)

while True:
    try:
        #Establish the connection
        #print("blocking")
        connectionSocket, clientAddr = serverSocket.accept()
        print ('Novo cliente conectado:', clientAddr)
    except timeout as timeOut_e:
        #print(timeOut_e)
        continue

    try:
        # receive a request
        messageBytes, msgAddr = connectionSocket.recvfrom(2048)

        if not messageBytes:
            connectionSocket.close()
            continue

        print("INPUT DEBUG:\n---------------------\n",
              messageBytes.decode(),
              "\n---------------------\n")
        message = messageBytes.decode()

        method = message.split()[0]
        print("Método:", method)

        filename = message.split()[1]
        print("Requisitou:", filename)
        
        if(method == "GET"): # GET method handling
            # if in initial page, redirect to index.html
            if(filename == "/"):
                print("Redirecionando para o index")
                filename = "/index.html"
            
            f = open(filename[1:])
            outputdata = f.read()
            f.close()

            #Send one HTTP header line into socket
            header = "HTTP/1.1 200 OK\r\n"
            # time
            headerLines ="Date: " + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) + "\r\n"
            # server
            headerLines += "Server: Python_Socket\r\n" 
            # content length
            headerLines += "Content-Length: " + str(os.path.getsize(filename[1:])) + "\r\n"
            # content type
            fileType = filename.split('.')[-1]
            if(fileType == "html"):
                headerLines += "Content-Type: text/html\r\n"
            else:
                headerLines += "Content-Type: " + fileType + "\r\n"
            # connection close (connection will be closed after the response)
            headerLines += "Connection: close\r\n\r\n"
            responseHeader = header + headerLines
            print("Resposta enviada:", responseHeader)

            outputdata = responseHeader + outputdata
            #Send the content of the requested file to the client
            for i in range(0, len(outputdata)):
                connectionSocket.send(outputdata[i].encode())
            connectionSocket.send("\r\n".encode())
            connectionSocket.close()
        elif(method == "POST"): # POST method handling
            # format the request body to a list of fields sended
            requestBody = unquote(message.split("\r\n\r\n")[1]).split('&')
            fieldDict = dict()
            # get the key and value of each field
            for key, value in [field.split('=') for field in requestBody]:
                #print(key, " = ", value)
                fieldDict[key] = value

                
        else: # raises execption for unknown method
            raise IOError("Unknown Method")
    except IOError as e:
        print("Capturada uma exceção:\n     ", e)
        # error 404 Not Found
        if(e.errno == 2):
            #try to send one HTTP 404 header line into socket
            try:
                header = "HTTP/1.1 404 Not Found\r\n"
                # time
                headerLines ="Date: " + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) + "\r\n"
                # server
                headerLines += "Server: Python_Socket\r\n"
                # content type
                headerLines += "Content-Type: text/html\r\n"
                # connection close (connection will be closed after the response)
                headerLines += "Connection: close\r\n\r\n"
                
                responseHeader = header + headerLines
                print(responseHeader)
                outputdata = responseHeader + (
                    "<!doctype html><html> <head></head>" +
                        "<body>" +
                            "<center><h1>Error 404: Not found</h1></center>" +
                        "</body>" + 
                    "</html>")
                #print(outputdata)
                #Send response message for file not found
                for i in range(0, len(outputdata)):
                    connectionSocket.send(outputdata[i].encode())
                connectionSocket.send("\r\n".encode())
            except ConnectionError as conn_e:
                print("Capturado um erro de conexão:", conn_e)
        #Close client socket
        connectionSocket.close()
        continue

#closeServer()
# should not reach this section of code...
# all exceptions should be treated and connections closed