from socket import *

def sendAvailableWords():
    words = bytearray()

    for word in list(portToEnglish.keys()):
        words.extend((word + ' ').encode())

    connectionSocket.send(words)

def sendInvalidMessage():
    connectionSocket.send(convertToBytes('INVALID'))

def convertToBytes(string):
    return bytearray(string, 'utf-8')

def convertToString(byte):
    return str(message, encoding = 'utf-8')

portToEnglish = {
    'enlace': 'link',
    'roteador': 'router',
    'pacote': 'packet',
    'rede': 'network',
    'protocolo': 'protocol',
    'hospedeiro': 'host',
    'mensagem': 'message',
    'propagação': 'propagation',
    'atraso': 'delay',
    'transmissão': 'transmission',
}

portToFrench = {
    'enlace': 'lien',
    'roteador': 'routeur',
    'pacote': 'paquet',
    'rede': 'réseau',
    'protocolo': 'protocole',
    'hospedeiro': 'hôte',
    'mensagem': 'message',
    'propagação': 'propagation',
    'atraso': 'retard',
    'transmissão': 'transmission',
}

serverPort = 80
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))

serverSocket.listen(1)
print('Servidor está pronto para receber...')

connectionSocket, address = serverSocket.accept()
print ('Conectado com: ', address)

choice, clientAddress = connectionSocket.recvfrom(2048)

if int(choice) == 1:
    dictionary = portToEnglish    
elif int(choice) == 2:
    dictionary = portToFrench
else:
    sendInvalidMessage()
    exit()

# envia as palavras disponiveis no dicionario
sendAvailableWords()

while 1:
    message, clientAddress = connectionSocket.recvfrom(2048)
    key = convertToString(message)

    # se receber SAIR, encerra a conexao
    if not message:
        break

    # se o cliente quiser uma chave que nao existe no dicionario, envia uma resposta de invalidez
    if key not in dictionary:
        sendInvalidMessage()
        break

    connectionSocket.send(convertToBytes(dictionary[key]))

connectionSocket.close()
