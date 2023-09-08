#import socket module
from socket import *
import sys # In order to terminate the program
import os # get file details
import time # to send time in response header lines
import signal # for manually closing the socket
from urllib.parse import unquote # for decoding url coded to UTF-8
import threading # creates client session threads 
import csv

print("\nDNS:", )
DNS_IP_LAN = gethostbyname_ex("")
DNS_IP_WAN = gethostbyname_ex("renanmalv.ddns.net")
print("IP de DNS LAN:", DNS_IP_LAN)
print("IP de DNS WAN:", DNS_IP_WAN)

#Prepare a sever socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverAddr = DNS_IP_LAN[2][0]
serverPort = 80
serverSocket.bind((serverAddr, serverPort))
serverSocket.listen(5)
serverSocket.settimeout(5.0)
sessions = {}
print("\nServidor inicializado em", serverSocket.getsockname())

def getUser(addr):
    for user, loggedAddr in sessions.items():
        if addr[0] == loggedAddr[0]:
            return user
    return None

def closeServer(sigNumber, _):
    print("Encerrando servidor...", "Sinal:", signal.Signals(sigNumber).name)
    serverSocket.close()
    sys.exit()#Terminate the program after sending the corresponding data

# authenticate credentials
def authLogIn(user, pswd):
    with open("users.csv", "r") as users:
        reader = csv.DictReader(users)
        for userInfo in reader:
            if(user == userInfo["user"] and pswd == userInfo["pass"]):
                return True
    return False
    
# authenticate connection
def authConn(user, clientAddr):
    #print(clientAddr, "\n", sessionAddr)
    userAddr = sessions.get(user)
    print("Tentando autenticar", user, userAddr)
    if userAddr is not None:
        if userAddr[0] == clientAddr[0]:
            return True 
    print("não autenticado!")
    return False

    
def sendPage(filename, connectionSocket, user, clientAddr):
    # if in initial page, redirect to index.html
    outputdata = ""
    if(filename == "/"):
        print("Redirecionando para o index")
        filename = "/index.html"
    
    if(filename == "/user"):
        if authConn(user, clientAddr):
            content = (
                "<br>" +
                "Conectado como " + user + 
                "<br>" + 
                "<br>" + 
                "<form action=\"logout\" method=\"post\" name=\"Logout\">" + 
                "<input name=\"submit\" type=\"submit\" value=\"logout\" style=\"height:50px;width:200px\"/>" +
                "</form>" +
                "<br>" +
                "<hr>" +
                "<br>" + 
                "DNS (LAN): " + ''.join(DNS_IP_LAN[0]) +
                "<br>" + 
                "IP: " + ''.join(DNS_IP_LAN[2]) +
                "<br>" +
                "<br>" +
                "DNS (WAN): " + ''.join(DNS_IP_WAN[0]) +
                "<br>" + 
                "IP: " + ''.join(DNS_IP_WAN[2])
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

def sessionThread(connectionSocket, clientAddr):
    user = getUser(clientAddr)
    try:
        # receive a request
        messageBytes, msgAddr = connectionSocket.recvfrom(2048)

        if not messageBytes:
            connectionSocket.close()
            return

        #print("INPUT DEBUG:\n---------------------\n",
        #      messageBytes.decode(),
        #      "\n---------------------\n")
        message = messageBytes.decode()

        method = message.split()[0]
        print("Método:", method)

        filename = message.split()[1]
        print("Requisitou:", filename)
        
        if(method == "GET"): # GET method handling
            sendPage(filename, connectionSocket, user, clientAddr)
        
        elif(method == "POST"): # POST method handling
            # format the request body to a list of fields sended
            requestBody = unquote(message.split("\r\n\r\n")[1]).split('&')
            fieldDict = dict()
            # get the key and value of each field
            for key, value in [field.split('=') for field in requestBody]:
                #print(key, " = ", value)
                fieldDict[key] = value
            
            action = fieldDict.pop("submit")
            if(action == "login"):
                # log out if there is a user already connected
                if(user):
                    sessions.pop(user)
                auth = authLogIn(fieldDict["user"], fieldDict["pass"])
                if auth:
                    user = fieldDict["user"]
                    sessions[user] = clientAddr
                    print("\nSessão", user, "iniciada com sucesso!\n")
                    sendRedirect("/user", connectionSocket)
                else:
                    sendRedirect("/404", connectionSocket)
            elif(action == "logout"):
                if authConn(user ,clientAddr):
                    print("Logging", user, "out...")
                    sessions.pop(user)
                    sendRedirect("/", connectionSocket)
                else:
                    sendRedirect("/404", connectionSocket)
            elif(action == "register"):
                # Open the CSV file to register a user
                with open("users.csv", "a", newline='') as db:
                    writer = csv.DictWriter(db, fieldnames=fieldDict.keys())
                    writer.writerow(fieldDict)
                print("\nUsuário", fieldDict["user"], "registrado com sucesso!\n")
                sendRedirect("/", connectionSocket)
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
        return

while True:
    try:
        # Establish the connection
        #print("blocking")
        connectionSocket, clientAddr = serverSocket.accept() # create exception on timeout
        print ("Nova conexão com o cliente:", clientAddr)
        # create a new client session thread
        print("\n Usuários logados:", sessions, "\n")
        threading.Thread(target=sessionThread, args=(connectionSocket, clientAddr)).start()
    except timeout as timeOut_e:
        #print(timeOut_e)
        continue
    
#closeServer()
# should not reach this section of code...
# all exceptions should be treated and connections closed