import socket
import sys
import traceback
import threading
import datetime
import platform  # To get OS - platform.system()+platform.release()
                 # To get Hostname - platform.node()

peerList ={}        # Dictionary to store all peer related information
# activepeerList = {} # Dictionary to store active peers
peerListCounter = 0 # Variable to hold peerList
cookieCounter = 1   # Cookies are given chronologically

def main():
    startServer()

def startServer():
    host = ""
    port = 8888         # RS port
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    
    try:
        serverSocket.bind((host, port))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        exit()

    serverSocket.listen(6)       # Can connect to 6 peers

    while True:         # Keep accepting connections
        connection, addr = serverSocket.accept()
        ip = str(addr[0])
        port = str(addr[1])
        print("Connected with " + ip + ":" + port)
        try:
            threading.Thread(target=client_thread, args=(connection, ip, port)).start()  
        except:
            traceback.print_exc()
    serverSocket.close()


def client_thread(connection, ip, port, max_buffer_size = 8120):
    is_active = True

    while is_active:
        client_input = receive_input(connection, max_buffer_size)
        if "--QUIT--" in client_input:
            connection.close()
            print("Connection " + ip + ":" + port + " closed")
            is_active = False         

        else:
            message_response = P2PmessageParser(client_input,ip)
            connection.sendall(message_response.encode("utf8"))
            
def make_peer_inactive(cookie):  # Makes peer inactive by setting flag as False
    for i,val in peerList.items():  
             try:
                 if(peerList[i]['cookie']== cook ):
                     peerList[i]['flag']= False                    
                     break
             except:
                 continue
    # print(peerList)


def receive_input(connection, max_buffer_size):
    recvdMessage = connection.recv(max_buffer_size)

    decoded_input = recvdMessage.decode("utf8").rstrip()  
    result = str(decoded_input.upper())
    print(result)
    return result

def P2PmessageParser(input_message,ip): # Parses message received
    global cookieCounter
    global peerListCounter

    messageLoc = input_message
    method = messageLoc.split()[1]

    if(method == 'LEAVE'):
        print("leaving")
        cookie1 = messageLoc.split('COOKIE: ')[1]
        cook = cookie1.split()[0]
        cookie1 = messageLoc.split('COOKIE: ')[1]
        cook = cookie1.split()[0]
        for i,val in peerList.items():
             try:
                 if(peerList[i]['cookie']== int(cook) ):
                     peerList[i]['flag']= False        
                     break
             except:
                 continue
        response = "LEAVE OK P2P-DI/0.1\r\n"
        # print(activepeerList)
        
    if(method == 'REGISTER'):
        line = messageLoc.split('RFCSERVERPORT: ')[1]
        port_number = line.split()[0]
        peer=dict( name = ip , cookie = cookieCounter, flag = True, TTL = 7200, portNumber = port_number, numRegister = 1, lastRegister = str(datetime.datetime.now()))
        peerList[peerListCounter] = peer    
        response = "REGISTER OK P2P-DI/0.1\r\nCookie: " +str(cookieCounter)+"\r\n"
        timer = threading.Timer(7200.0, make_peer_inactive, args = [cookieCounter])  # Starts timer for TTL
        timer.start()
        peerListCounter += 1
        cookieCounter += 1

    if(method == 'KEEPALIVE'):
        cookie1 = messageLoc.split('COOKIE: ')[1]
        cook = cookie1.split()[0]
        for i,val in peerList.items():
             try:
                 if(peerList[i]['cookie']== cook ):
                     peerList[i]['TTL']=7200                    
                     break
             except:
                 continue
        response = "KEEPALIVE OK P2P-DI/0.1\r\n"
    if(method == 'PQUERY'):  
        activepeerList = {}  
        cookie1 = messageLoc.split('COOKIE: ')[1]
        cook = int(cookie1.split()[0])
        # print(cookie1)
        activeCount = 1
        # print(peerList)
        for i,val in peerList.items():
                  if((peerList[i]['flag']== True) & (peerList[i]['cookie']!= cook) ):
                     activePeer = dict(name = peerList[i]['name'], portNumber = peerList[i]['portNumber'])            
                     activepeerList[activeCount] = activePeer
                     activeCount += 1
        response = "PQUERY OK P2P-DI/0.1\r\nList: "+str(activepeerList)+"\r\n" 
        # print(activepeerList)
   
    return response
    


if __name__ == "__main__":
    main()