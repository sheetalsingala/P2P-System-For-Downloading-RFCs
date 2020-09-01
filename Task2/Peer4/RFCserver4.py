#!/usr/bin/python3
import socket
import threading
import pickle
import time
import socket
import ast
import platform     # To get OS - platform.system()+platform.release()
                    # To get Hostname - platform.node()
platform_values = platform.system()+ " " + platform.release()
import errno
import time
import os
from matplotlib import pyplot as plt 

OS = platform.node()
  
port = 65406

A= list(range(60))  # X - axis
B=[]

plt.xlabel('File number') 
plt.ylabel('Time taken (secs)') 

RShost = "192.168.1.207"
RSport = 8888
lock_client=threading.Lock()
RFC_Index={
    24:["rfc24.txt", 7200, ['localhost']],
    25:["rfc25.txt", 7200, ['localhost']],
    27:["rfc27.txt", 7200, ['localhost']],
    28:["rfc28.txt", 7200, ['localhost']],
    29:["rfc29.txt", 7200, ['localhost']],
    30:["rfc30.txt", 7200, ['localhost']],
    31:["rfc31.txt", 7200, ['localhost']],
    32:["rfc32.txt", 7200, ['localhost']],
    33:["rfc33.txt", 7200, ['localhost']],
    34:["rfc34.txt", 7200, ['localhost']]

}

def downloadRFC(ip,port,fileN):
    dwnmsg = build_msg("GET: RFC_index- "+str(fileN)," GETRFC",OS,platform_values)
    downloadmsg= dwnmsg.encode('utf-8')
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s1.connect((ip, int(port)))
    s1.send(downloadmsg)
    with open('rfc'+str(fileN)+'.txt', 'wb') as f:
        while True:               
            print('receiving data...')
            data = s1.recv(1024)
            if not data:
                break
            f.write(data)
        f.close()
        print('File Downloaded successfully')
    s1.close() 


def RS_client_socket(clients):
    connected = False   
    while not connected:  
    # attempt to reconnect, otherwise sleep for 2 seconds  
        try:   
            clients.connect( ( RShost, RSport ) )  
            connected = True  

        except socket.error  as error:
            if error.errno == errno.ECONNREFUSED:
                print(os.strerror(error.errno))
            else:
                raise 
            time.sleep( 2 )  


def sendRS_msg(clients,messageL):
    clients.sendall(messageL.encode("utf8"))
    reply = clients.recv(8120).decode("utf8")
    cookie= P2CmessageParser(reply)
     


def P2CmessageBuilder(message_type,port_number):
    if(message_type == 2):
        messageNew = "GET Leave P2P-DI/0.1\r\nCookie: "+ str(cookie)+"\r\nHost: " + OS +"\r\nOS: "+platform_values+"\r\n"
    if(message_type == 1):
        messageNew = "GET Register P2P-DI/0.1\r\nRFCServerPort: " +str(port)+"\r\nHost: " + OS+"\r\nOS: "+platform_values+"\r\n"
    if(message_type == 3):
        messageNew = "GET PQuery P2P-DI/0.1\r\nCookie: "+ str(cookie)+"\r\nHost: " + OS +"\r\nOS: "+platform_values+"\r\n"      
    if(message_type == 4):
        messageNew = "GET keepAlive P2P-DI/0.1\r\nCookie: "+ str(cookie)+"\r\nHost: " + OS+"\r\nOS: "+platform_values+"\r\n"   
 
    return messageNew

def quit():
    clientSocket3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    RS_client_socket(clientSocket3)
    messageL = P2CmessageBuilder(2, None)
    sendRS_msg(clientSocket3,messageL)
    leave(clientSocket3)
    
def P2CmessageParser(reply_message):
    global cookie
    global peerlist
    messageLoc = reply_message
    method = messageLoc.split()[0]
    if(method == 'REGISTER'):
        cookie = messageLoc.split()[4]     
    if(method == 'PQUERY'):
        peerlist = ast.literal_eval(messageLoc.split('List: ')[1])
        print(peerlist)
    return cookie

def register():
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    RS_client_socket(clientSocket)
    messageL = P2CmessageBuilder(1, port)
    sendRS_msg(clientSocket,messageL)
    leave(clientSocket)

def PQuery():
    clientSocket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    RS_client_socket(clientSocket1)
    messageL = P2CmessageBuilder(3,None)
    sendRS_msg(clientSocket1,messageL)
    leave(clientSocket1)

def KeepAlive():
    clientSocket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    RS_client_socket(clientSocket2)
    messageL = P2CmessageBuilder(4, None)
    sendRS_msg(clientSocket2,messageL)
    leave(clientSocket2)
    

def leave(clients):
    clients.send(b'--quit--') 
    clients.close()
    

    
# # Always called, even if exception is raised in try block
def update_RFC(arg1, ip_address,port):
    
    for k, v in arg1.items():
        lock_client.acquire()
        if k in RFC_Index:
            RFC_Index[k][2].append(ip_address)
        else:
            # create new entry for rfc
            tinit = time.clock()
            RFC_Index[k]=v
            downloadRFC(ip_address,port,k)
            tfinal = time.clock()
            ttot = tfinal - tinit
            B.append(ttot)
        lock_client.release()
    print(B)
    print(len(B))
    print(RFC_Index)

def Handle_request(connection, addr):
    msg = connection.recv(4096)
    msg_s = msg.decode('utf-8')
    first_line = msg_s.split("\n")[0]
    method = first_line.split(":")[0]
    if method == "GET":
        second_line = msg_s.split("\n")[1]
        types  = second_line.split(":")[1].lstrip()[:-1]
        if types == "RFCQuery":
            lock_client.acquire()
            send_msg = pickle.dumps(RFC_Index)
            connection.send(send_msg)
            lock_client.release()
        elif types == "GETRFC" :
            files = msg_s.split("\r")[0]
            fileNum = files.split('- ')[1]
            filename = 'rfc'+str(fileNum)+'.txt'
            f = open(filename,'rb')
            l = f.read(1024)
            print('Sending file..)')
            while(l):
                connection.send(l)
                l = f.read(1024)
            f.close()
        connection.close()

def build_msg(arg1, arg2, arg3,arg4):
    msg = arg1+"\r\ntypes: "+arg2+"\r\nHost: "+arg3+"\r\nOS: "+arg4+"\r\n"
    return (msg)

def socketFunc(msg, IP, port):
    IPaddr = IP
    portn = port
    print("client3")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP, int(port)))
    message = msg.encode('utf-8')
    s.send(message)
    recvd_rfc = b''
    while True:
        rfc_recv=s.recv(8192)
        if not rfc_recv:
            break
        recvd_rfc+=rfc_recv
    s.close() 
    msg_dict = pickle.loads(recvd_rfc)
    update_RFC(msg_dict,IPaddr,int(portn))

def request_RFC_index():
    msg = build_msg("GET: RFC_index ","RFCQuery",OS,platform_values)
    PQuery()
    print(peerlist)
    time.sleep(2)
    for i,k in peerlist.items():
        print("name",peerlist[i]['name'])
        print("port",peerlist[i]['portNumber'])
        socketFunc(msg, peerlist[i]['name'], peerlist[i]['portNumber'])

def client_code():
    register()
    time.sleep(15)
    request_RFC_index()


if __name__ == '__main__':

## client thread
    new_Client = threading.Thread(target = client_code, args=())

    new_Client.start()

    threads = []

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
    print('Socket successfully created')
    s.bind(('', port))
    print('socket binded to %s' %(port)) 
    s.listen(5)	 
    print ('socket is listening')	
    while True:
        try:
            connection, addr = s.accept()
        
            new_thread = threading.Thread(target = Handle_request, args=(connection, addr))
            new_thread.start()

            threads.append(new_thread)
        except KeyboardInterrupt:
            break
    print(len(threads))
    for thread in threads:
        thread.join()
    print('all threads are joined')

