# Introduction to Computer Networks, NTUEE (Spring 2018)
# Video Streaming Client
# Reference: RFC 2326 (RTSP) / RFC 3550 (RTP)
# Reference: https://www.csee.umbc.edu/~pmundur/courses/CMSC691C/lab5-kurose-ross.html
# Reference: https://gist.github.com/jn0/8b98652f9fb8f8d7afbf4915f63f6726

# the following modules are required.
import io
import re
import time
import numpy
import socket
import random
import _thread
import tkinter as tk
from rtppacket import rtp_packet
from enum import Enum
from PIL import Image, ImageTk
#from rtp_packethead import rtpPacket
#from multiprocessing import Process

class C_(Enum):
    INIT = 0
    READY = 1
    PLAYING = 2

# RTSP requests

client_p, server_p = random.randint(6000/2,10000/2)*2, 0
state = C_.INIT
CSeq = 1
session = ''
t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
t.settimeout(5)

Request_URI = "rtsp://127.0.0.1/media/testing.mp4"

HOST = re.findall('://([0-9A-Za-z.]+)/', Request_URI)[0]
addr=(HOST,554)

def setup():
    global state, CSeq, client_p, server_p, session, t, frame_buffer 
    frame_buffer = []
    # test available methods
    optn = ("OPTIONS "+Request_URI+" RTSP/1.0\r\nCseq: "+str(CSeq)+"\r\n\r\n").encode()
    t.sendto(optn,addr)
    try: rstr = t.recv(4096)
    except ConnectionResetError:
        print("Server was down.")
        return False
    print(rstr.decode())
    # get Session, Control URL
    desc = ("DESCRIBE "+Request_URI+" RTSP/1.0\r\nCseq: "+str(CSeq+1)+"\r\n\r\n").encode()
    t.sendto(desc,addr)
    rstr = t.recv(4096)
    print(rstr.decode())
    ctrl_url = False
    vid_url = aud_url = ""
    for attr in rstr.decode().split("\r\n"):
        if(attr.startswith("m=video")): ctrl_url = True
        if(attr.startswith("a=control:") and ctrl_url):
            vid_url = attr[10:]
            break
    ctrl_url = False
    if(vid_url == "*"): vid_url = Request_URI
    elif(len(re.findall('^[A-Za-z]+://', vid_url))): pass
    else: vid_url = Request_URI + "/" + vid_url
    for attr in rstr.decode().split("\r\n"):
        if(attr.startswith("m=audio")): ctrl_url = True
        if(attr.startswith("a=control:") and ctrl_url):
            aud_url = attr[10:]
            break
    if(aud_url == "*"): aud_url = Request_URI
    elif(len(re.findall('^[A-Za-z]+://', aud_url))): pass
    else: aud_url = Request_URI + "/" + aud_url
    # setup and ready to receive RTP
    '''stup = ("SETUP "+aud_url+" RTSP/1.0\r\nCseq: "+str(CSeq+2)+"\r\nTransport: RTP/AVP;unicast;client_port="+str(client_p)+"-"+str(client_p+1)+"\r\n\r\n").encode()
    #print(stup.decode())
    t.sendto(stup,addr)
    rstr = t.recv(4096)
    session = re.findall(b'Session: ?([0-9A-Za-z]+)', rstr)[0].decode()
    print(rstr.decode())'''
    stup = ("SETUP "+vid_url+" RTSP/1.0\r\nCseq: "+str(CSeq+3)+"\r\nTransport: RTP/AVP;unicast;client_port="+str(client_p)+"-"+str(client_p+1)+"\r\n\r\n").encode()
    print(stup.decode())
    t.sendto(stup,addr)
    rstr = t.recv(4096)
    session = re.findall(b'Session: ?([0-9A-Za-z]+)', rstr)[0].decode()
    server_p = int(re.findall(b'\r\nTransport: .+;server_port=(\d+)', rstr)[0].decode())
    print(rstr.decode())
    CSeq += 4
    return True

def play():
    global state, CSeq, server_p, session, t
    plyy = ("PLAY "+Request_URI+" RTSP/1.0\r\nCseq: "+str(CSeq)+"\r\nSession: "+session+"\r\nRange: "+'npt=0.123-4.567'+"\r\n\r\n").encode()
    #print(plyy.decode())
    t.sendto(plyy,addr)
    try:
        rstr = t.recv(4096)
    except socket.timeout:
        print("Timeout, you need to SETUP again.")
        return False
    print(rstr.decode())
    CSeq += 1
    return True

def pause():
    global state, CSeq, session, t
    paus = ("PAUSE "+Request_URI+" RTSP/1.0\r\nCseq: "+str(CSeq)+"\r\nSession: "+session+"\r\n\r\n").encode()
    #print(paus.decode())
    t.sendto(paus,addr)
    try:
        rstr = t.recv(4096)
    except socket.timeout:
        print("Timeout, you need to SETUP again.")
        return False
    print(rstr.decode())
    CSeq += 1
    return True

def teardown():
    global state, CSeq, session, t
    tdwn = ("TEARDOWN "+Request_URI+" RTSP/1.0\r\nCseq: "+str(CSeq)+"\r\nSession: "+session+"\r\n\r\n").encode()
    t.sendto(tdwn,addr)
    try:
        rstr = t.recv(4096)
    except socket.timeout:
        print("Timeout.")
        return False
    print(rstr.decode())
    CSeq += 1
    return True

def set_param(event):
    global state, CSeq, t
    if(not len(e.get())): return False
    payload = "ctrl: "+e.get()
    setp = ("SET_PARAMETER "+Request_URI+" RTSP/1.0\r\nCseq: "+str(CSeq)+"\r\nContent-type: text/parameters\r\nContent-length: "+str(len(payload.encode()))+"\r\n\r\n"+payload).encode()
    t.sendto(setp,addr)
    rstr = t.recv(4096)
    print(rstr.decode())
    CSeq += 1
    return True


# button events and state maintain

def c_setup():
    global state, current_point
    current_point = 0
    print("Setup.")
    if(not setup()): return False
    if(state!=C_.PLAYING): state=C_.READY

def c_play():
    global state
    if(state==C_.INIT):
        print("No session!")
        return False
    print("Play the media.")
    play()
    state=C_.PLAYING
    _thread.start_new_thread(vid_display,())

def c_pause():
    global state
    if(state!=C_.PLAYING):
        print("Not playing!")
        return False
    print("Pause the media.")
    pause()
    state=C_.READY

def c_down():
    global state
    print("Teardown.")
    teardown()
    state=C_.INIT



def rtp_rec():
    global state, client_p, frame_buffer
    r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    r.bind(("", client_p))
    temp_sep = 0
    r.settimeout(5)
    while(True):
        try:
            packet, adr = r.recvfrom(65536) # limitation is 64KB
            if(adr[1]!=server_p): continue # ignore messages from wrong port
           # print("Recv",len(buffer_img),"bytes")

            rtppacket = rtp_packet()
            rtppacket.decode(packet)
            buffer_img = rtppacket.getpayload()
           # print("seq",rtppacket.seqnum())
            if rtppacket.seqnum() < temp_sep:
                continue
            elif rtppacket.seqnum() >= temp_sep:
               # print("buffer")
                frame_buffer.append(buffer_img)
                temp_sep = rtppacket.seqnum()
        except socket.timeout:
            print("RTP Timeout.")
            state=C_.READY

def vid_display():
    global state, w, current_point, frame_buffer
    time.sleep(1)
    while(state==C_.PLAYING):
        try:
            global disp
            print("frame_buffer: ",len(frame_buffer))
            print("current: ",current_point)
            disp = ImageTk.PhotoImage(Image.open(io.BytesIO(frame_buffer[current_point])).resize((wid,hei)))
           # print(current_point)
            current_point += 1
            w.configure(image=disp)
            w.image = disp # this line solves flickering problem.
        except OSError:
            print("Bad frame.")
            continue
        except IndexError: # frame_buffer is empty
            continue
    if(state==C_.INIT):
        w.configure(image=bk)
        w.image = bk
    else: # state==C_.READY
        w.configure(image=disp)
        w.image = disp



# generate GUI
master = tk.Tk()
master.title("RTSP Client")
master.resizable(False,False)

wid, hei = 480, 360
disp = bk = ImageTk.PhotoImage(Image.fromarray(numpy.zeros((hei,wid,3), numpy.uint8)))

w = tk.Label(master, image=bk)
w.grid(row=0, column=0, columnspan=4)

b = []
for i in range(4):
    tx={0:"SETUP",1:"PLAY",2:"PAUSE",3:"TEARDOWN"}.get(i)
    cmd={0:c_setup,1:c_play,2:c_pause,3:c_down}.get(i)
    b.append(tk.Button(master,text=tx,command=cmd,width=10,height=2))
    b[i].grid(row=1, column=i, sticky=tk.W+tk.E)

e = tk.Entry(master)
e.grid(row=2, column=0, columnspan=4, sticky=tk.W+tk.E)
e.bind("<Return>", set_param)

_thread.start_new_thread(rtp_rec,())

master.mainloop()