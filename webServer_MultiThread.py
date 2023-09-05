#import socket module
from socket import *
import sys # In order to terminate the program
import os # get file details
import time # to send time in response header lines
import signal # for manually closing the socket
from urllib.parse import unquote # for decoding url coded to UTF-8

#Prepare a sever socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverAddr = "192.168.0.4"
serverPort = 80
serverSocket.bind((serverAddr, serverPort))
serverSocket.listen(5)
serverSocket.settimeout(5.0)
user = ""
sessionAddr = {}
print('Servidor inicializado em ', serverSocket.getsockname())

def closeServer(sigNumber, _):
    print("Encerrando servidor...", "Sinal:", signal.Signals(sigNumber).name)
    serverSocket.close()
    sys.exit()#Terminate the program after sending the corresponding data

# authenticate credentials
def authLogIn(user, pswd):
    if(user == "renan@mail.com" and pswd == "pass"):
        return True
    else:
        return False
    
# authenticate connection
def authConn(clientAddr):
    #print(clientAddr, "\n", sessionAddr)
    if sessionAddr:
        if(clientAddr[0] == sessionAddr[0] and user != ""):
            return True
    
    return False

    
def sendPage(filename, connectionSocket, clientAddr):
    # if in initial page, redirect to index.html
    outputdata = ""
    if(filename == "/"):
        print("Redirecionando para o index")
        filename = "/index.html"
    
    if(filename == "/user"):
        if authConn(clientAddr):
            content = (
                "Conectado como " + user + 
                "<br>" + 
                "<form action=\"logout\" method=\"post\" name=\"Logout\">" + 
                "<input name=\"submit\" type=\"submit\" value=\"Log out\" style=\"height:50px;width:200px\"/>" +
                "</form>"
            )    
        else:
            content = "Não conectado!"

        outputdata = (
        "<!doctype html><html> <head><meta charset=\"utf-8\"></head>" +
            "<body>" +
                "<center><h1>" + 
                content + 
                "</h1></center>" +
            "</body>" + 
        "</html>"
        )
    else:
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
    headerLines += "Content-Length: " + str(len(outputdata.encode("UTF-8"))) + "\r\n"
    # content type
    fileType = filename.split('.')[-1]
    if(fileType == "html" or len(filename.split('.')) == 1):
        headerLines += "Content-Type: text/html\r\n"
    else:
        headerLines += "Content-Type: " + fileType + "\r\n"
    # connection close (connection will be closed after the response)
    headerLines += "Connection: close\r\n\r\n"
    
    responseHeader = header + headerLines
    outputdata = responseHeader + outputdata
    
    #Send the content of the requested file to the client
    for i in range(0, len(outputdata)):
        connectionSocket.send(outputdata[i].encode())
    connectionSocket.send("\r\n".encode())
    print("Resposta enviada:", responseHeader)
    connectionSocket.close()

def sendRedirect(filename, connectionSocket):
    outputdata = ''
    #Send one HTTP header line into socket
    header = "HTTP/1.1 303 See Other\r\n"
    # time
    headerLines ="Date: " + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) + "\r\n"
    # server
    headerLines += "Server: Python_Socket\r\n" 
    # content length
    headerLines += "Content-Length: " + '0' + "\r\n"
    # content type
    headerLines += "Content-Type: text/html\r\n"
    # Localização da url para redirecionamento
    headerLines += "Location: " + filename + "\r\n"
    # connection close (connection will be closed after the response)
    headerLines += "Connection: close\r\n\r\n"
    
    responseHeader = header + headerLines
    outputdata = responseHeader + outputdata
    
    #Send the content of the requested file to the client
    for i in range(0, len(outputdata)):
        connectionSocket.send(outputdata[i].encode())
    connectionSocket.send("\r\n".encode())
    print("Resposta enviada:", responseHeader)
    connectionSocket.close()

def send404(connectionSocket):
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

# prepare for handling SIGINT
signal.signal(signal.SIGINT, closeServer)

while True:
    try:
        #Establish the connection
        #print("blocking")
        connectionSocket, clientAddr = serverSocket.accept()
        print ("Nova conexão com o cliente:", clientAddr)
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
            sendPage(filename, connectionSocket, clientAddr)
        
        elif(method == "POST"): # POST method handling
            # format the request body to a list of fields sended
            requestBody = unquote(message.split("\r\n\r\n")[1]).split('&')
            fieldDict = dict()
            # get the key and value of each field
            for key, value in [field.split('=') for field in requestBody]:
                #print(key, " = ", value)
                fieldDict[key] = value
            
            if(fieldDict["submit"] == "Log+in"):
                auth = authLogIn(fieldDict["user"], fieldDict["pass"])
                if auth:
                    user = fieldDict["user"]
                    sessionAddr = clientAddr
                    print("\nSessão", user, "iniciada com sucesso!\n")
                    sendRedirect("/user", connectionSocket)
                else:
                    sendRedirect("/404", connectionSocket)
            elif(fieldDict["submit"] == "Log+out"):
                if authConn(clientAddr):
                    print("Logging", user, "out...")
                    user = ""
                    sessionAddr = ""
                    sendRedirect("/", connectionSocket)
                else:
                    sendRedirect("/404", connectionSocket)
            else:
                raise IOError("Unknown POST Submission")
                
        else: # raises execption for unknown method
            raise IOError("Unknown Method")
        
    except IOError as e:
        print("Capturada uma exceção:\n     ", e)
        # error 404 Not Found
        if(e.errno == 2):
            #try to send one HTTP 404 header line into socket
            try:
                send404(connectionSocket)
            except ConnectionError as conn_e:
                print("Capturado um erro de conexão:", conn_e)
        #Close client socket
        connectionSocket.close()
        continue

#closeServer()
# should not reach this section of code...
# all exceptions should be treated and connections closed