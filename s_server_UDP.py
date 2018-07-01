# Introduction to Computer Networks, NTUEE (Spring 2018)
# Video Streaming Server
# Reference: RFC 2326 (RTSP) / RFC 3550 (RTP)
# Reference: https://www.csee.umbc.edu/~pmundur/courses/CMSC691C/lab5-kurose-ross.html
# Reference: https://gist.github.com/jn0/8b98652f9fb8f8d7afbf4915f63f6726

# the following modules are required.
import io
import re
import cv2
import time
import socket
import random
import _thread
from mod import face
from enum import Enum
from PIL import Image
from time import ctime
from rtppacket import rtp_packet
#from rtp_packethead import rtp_packethead    

class C_(Enum):
    INIT = 0
    READY = 1
    PLAYING = 2

state = C_.INIT
CSeq = 0

HOST, PORT = "", 554
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((HOST,PORT))

t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
t.bind(("",7428))
t.settimeout(0)

session = ''

cap_sig = False
face_sig = False
cap = cv2.VideoCapture()
frm = 0
t_pause = 0


def get_file(src):
    f = open(src, "rb")
    ret = f.read()
    f.close()
    return ret

def kill_rtp():
    global cap_sig
    cap_sig = True
    time.sleep(0.5) # ensure rtp_send was terminated
    cap_sig = False

def init_vid(src):
    global cap_sig, cap, frm, t_pause
    kill_rtp()
    if(cap.isOpened()): cap.release()
    _thread.start_new_thread(rtp_send,()) # ensure cap is created after rtp_send
    if(src != ""): cap.open(src)
    frm = cap.get(cv2.CAP_PROP_FPS) # FPS of webcam is 0
    t_pause = 0



def makertp(payload, framenumber):
    version = 2 
    padding = 0
    extionsion = 0 
    cc = 0
    marker = 0
    pt = 26 
    seqnum = framenumber
    ssrc = 0
    rtppacket = rtp_packet()
    #print(payload)
    rtppacket.encode(version, padding, extionsion, cc, seqnum, marker, pt, ssrc, payload)
    
    return rtppacket.getPacket()

img_dummy = get_file("i_loading.jpg")

def img_proc(image):
    if(face_sig): image = face.face_proc(cv2.resize(image, (240,180)))
    return image

def rtp_send():
    global state, t, cap, frm, t_pause, address, c_port
    # if(cap.isOpened()): cap.set(cv2.CAP_PROP_POS_FRAMES,int(frm*t_pause))
    while(state == C_.PLAYING):
        rtp_pkg = img_dummy
        packet_index = 0
        if(cap_sig): # cap is unavailable
            return
        elif(cap.isOpened()):
            retval,im = cv2.VideoCapture.read(cap)
            if(not retval):
                print("Video was end, changing or unavailable.")
                cap.release()
                continue
            buffer = io.BytesIO()
            
            packet_index += 1
            
            im = img_proc(im)
            Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).save(buffer, format='JPEG')
            rtp_pkg = buffer.getvalue()
            #print(rtp_pkg)
        else:
            time.sleep(0.5) # show img_dummy
            packet_index += 1
       # print("Send",len(rtp_pkg),"bytes")
        if(len(rtp_pkg) >= 65536): print("The segment was too large!")
        else:
            try:
               # print("Send", len(makertp(rtp_pkg, packet_index)), "bytes")
                t.sendto(makertp(rtp_pkg,packet_index), (address[0],c_port))
                
            except NameError: pass

init_vid("") # no video was opened

print("Server is ready.")

while(True):
    message, address = s.recvfrom(4096)
    method = message.decode().split(" ")[0]
    req_uri = message.decode().split(" ")[1]
    cseq = re.findall('Cseq: (.+)', message.decode())[0]
    print(method+" "+cseq)
    response = "RTSP/1.0 200 OK\r\n"
    response += ("Cseq: "+cseq+"\r\n")
    if(method=='OPTIONS'): #required
        response += "Public: DESCRIBE, SETUP, TEARDOWN, PLAY, PAUSE\r\n\r\n"
    elif(method=='DESCRIBE'): #recommended
        response += "Content-Type: application/sdp\r\n"
        content = "v=0"
        content += ("\r\no="+"mymedia"+(" "+str(int(time.time())))*2+" IN IP4 127.0.0.1")
        content += ("\r\ns=RTSP Session")
        #content += ("\r\nm=audio "+"0 RTP/AVP 0") # PCM mu-law RFC3551
        #content += ("\r\na=control:aud")
        content += ("\r\nm=video "+"0 RTP/AVP 26") # Motion JPEG RFC2435
        content += "\r\na=control:vid"
        response += ("Content-Length: "+str(len(content.encode()))+"\r\n\r\n"+content)
    elif(method=='SETUP'): #required
        session = str(random.randint(8388609,16777216))
        c_port = int(re.findall('\r\nTransport: .+;client_port=(\d+)', message.decode())[0])
        response += ("Session: "+session+";timeout=60\r\n")
        response += ("Transport: RTP/AVP;unicast;client_port="+str(c_port)+"-"+str(c_port+1)+";server_port=7428-7429\r\n\r\n")
        state = C_.READY
    elif(method=='TEARDOWN'): #required
        c_sess = re.findall('\r\nSession: ([^\r\n]+)', message.decode())[0]
        session = ''
        response += "\r\n"
        t_pause = 0
        state = C_.INIT
    elif(method=='PLAY'): #required
        c_sess = re.findall('\r\nSession: ([^\r\n]+)', message.decode())[0]
        prange = re.findall('\r\nRange: ([^\r\n]+)', message.decode())[0]
        response += ("RTP-Info: "+"url="+req_uri+"/streamid=0;seq=45102"+"\r\n\r\n")
        #t_pause = float(re.findall('npt=([\d.]+)', prange)[0]) # client side is incomplete
        state = C_.PLAYING
        kill_rtp()
        _thread.start_new_thread(rtp_send,())
    
    elif(method=='PAUSE'): #recommended
        c_sess = re.findall('\r\nSession: ([^\r\n]+)', message.decode())[0]
        response += ("\r\n")
        state = C_.PLAYING
    elif(method=='SET_PARAMETER'): #optional
        try:
            ctrl = re.findall('\r\n\r\nctrl: ([^\r\n]+)', message.decode())[0]
            ctrl_u = ctrl.upper() # Uppercase
            s.sendto(response.encode(), address) # response before processing
            if  (len(re.findall('^STREAM', ctrl_u)) or len(re.findall('^MOVIE', ctrl_u))):
                img_dummy = get_file("i_loading.jpg")
                face_sig = False
                init_vid("i_test.mp4")
            elif(len(re.findall('^CAMERA', ctrl_u))):
                img_dummy = get_file("i_loading.jpg")
                face_sig = False
                init_vid(0)
            elif(len(re.findall('^MENU', ctrl_u))):
                img_dummy = get_file("i_loading.jpg")
                face_sig = False
                init_vid("")
            elif(len(re.findall('^FACE', ctrl_u))):
                img_dummy = get_file("i_face-recog.png")
                init_vid("")
                time.sleep(1)
                face_sig = True
                init_vid(0)
            elif(len(re.findall('^@.', ctrl_u))):
                print("danmaku received:"+ctrl[1:])
                # need further works
            else: pass
        except IndexError:
            response = "RTSP/1.0 451 Invalid Parameter\r\n"
            response += "Content-type: text/parameters\r\n"
            content = re.findall('\r\n([^:]+)', message.decode())[0]
            response += ("Content-Length: "+str(len(content.encode()))+"\r\n\r\n"+content)
    else: response = "RTSP/1.0 405 Method Not Allowed\r\n\r\n"
    if(method!='SET_PARAMETER'): s.sendto(response.encode(), address)