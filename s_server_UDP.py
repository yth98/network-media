# Introduction to Computer Networks, NTUEE (Spring 2018)
# Author: Yang, Tsung Hsien b06901031@ntu.edu.tw
# Reference: RFC 2326 (RTSP) / RFC 3550 (RTP) / RFC 4566 (SDP)
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
t_start = time.clock() # Discard return value of first call.
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
    global cap_sig, cap, frm, t_start, t_pause
    kill_rtp()
    if(cap.isOpened()): cap.release()
    _thread.start_new_thread(rtp_send,()) # ensure cap is created after rtp_send
    if(src != ""): cap.open(src)
    frm = cap.get(cv2.CAP_PROP_FPS) # FPS of webcam is 0
    t_start = time.clock()
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
    while(state == C_.PLAYING):
        rtp_pkg = img_dummy
        packet_index = 0
        if(cap_sig): # cap is unavailable
            return
        elif(cap.isOpened()):
            cap.set(cv2.CAP_PROP_POS_FRAMES,int(frm*(time.clock()-t_start)))

            retval,im = cv2.VideoCapture.read(cap)
            if(not retval):
                print("Video was end, changing or unavailable.")
                t_pause = 0
                state = C_.READY
                return
            buffer = io.BytesIO()
#         
            packet_index += 1

            im = img_proc(im)
            Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)).save(buffer, format='JPEG')
            rtp_pkg = buffer.getvalue()
            #print(rtp_pkg)
        else:
            time.sleep(0.5) # show img_dummy
       # print("Send",len(rtp_pkg),"bytes")
        if(len(rtp_pkg) >= 65536): print("The segment was too large!")
        else:
            try: 
                print("Send", len(makertp(rtp_pkg, packet_index)), "bytes")
                t.sendto(makertp(rtp_pkg,packet_index), (address[0],c_port))
                
            except NameError: pass
        time.sleep(0.002)

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
        t_start = time.clock() - t_pause
        state = C_.PLAYING
        kill_rtp()
        _thread.start_new_thread(rtp_send,())
    
    elif(method=='PAUSE'): #recommended
        c_sess = re.findall('\r\nSession: ([^\r\n]+)', message.decode())[0]
        response += ("\r\n")
        t_pause = time.clock() - t_start # INCORRECT & need to modify! t_pause should be recorded by client.
        state = C_.PLAYING
    elif(method=='SET_PARAMETER'): #optional
        try:
            ctrl = re.findall('\r\n\r\nctrl: ([^\r\n]+)', message.decode())[0]
            ctrl_u = ctrl.upper() # Uppercase
            s.sendto(response.encode(), address) # move up the response
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
                time.sleep(3)
                face_sig = True
                init_vid(0)
            else: pass # Overlaid video comment (danmaku) ?
        except IndexError:
            response = "RTSP/1.0 451 Invalid Parameter\r\n"
            response += "Content-type: text/parameters\r\n"
            content = re.findall('\r\n([^:]+)', message.decode())[0]
            response += ("Content-Length: "+str(len(content.encode()))+"\r\n\r\n"+content)
    else: response = "RTSP/1.0 405 Method Not Allowed\r\n\r\n"
    if(method!='SET_PARAMETER'): s.sendto(response.encode(), address)




'''

import java.io.*;
import java.net.*;
import java.awt.*;
import java.util.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.Timer;

public class Server extends JFrame implements ActionListener {

  //RTP variables:
  //----------------
  DatagramSocket RTPsocket; //socket to be used to send and receive UDP packets
  DatagramPacket senddp; //UDP packet containing the video frames

  InetAddress ClientIPAddr; //Client IP address
  int RTP_dest_port = 0; //destination port for RTP packets  (given by the RTSP Client)

  //GUI:
  //----------------
  JLabel label;

  //Video variables:
  //----------------
  int imagenb = 0; //image nb of the image currently transmitted
  VideoStream video; //VideoStream object used to access video frames
  static int MJPEG_TYPE = 26; //RTP payload type for MJPEG video
  static int FRAME_PERIOD = 100; //Frame period of the video to stream, in ms
  static int VIDEO_LENGTH = 500; //length of the video in frames

  Timer timer; //timer used to send the images at the video frame rate
  byte[] buf; //buffer used to store the images to send to the client

  //RTSP variables
  //----------------
  //rtsp states
  final static int INIT = 0;
  final static int READY = 1;
  final static int PLAYING = 2;
  //rtsp message types
  final static int SETUP = 3;
  final static int PLAY = 4;
  final static int PAUSE = 5;
  final static int TEARDOWN = 6;

  static int state; //RTSP Server state == INIT or READY or PLAY
  Socket RTSPsocket; //socket used to send/receive RTSP messages
  //input and output stream filters
  static BufferedReader RTSPBufferedReader;
  static BufferedWriter RTSPBufferedWriter;
  static String VideoFileName; //video file requested from the client
  static int RTSP_ID = 123456; //ID of the RTSP session
  int RTSPSeqNb = 0; //Sequence number of RTSP messages within the session

  final static String CRLF = "\r\n";

  //--------------------------------
  //Constructor
  //--------------------------------
  public Server(){

    //init Frame
    super("Server");

    //init Timer
    timer = new Timer(FRAME_PERIOD, this);
    timer.setInitialDelay(0);
    timer.setCoalesce(true);

    //allocate memory for the sending buffer
    buf = new byte[15000];

    //Handler to close the main window
    addWindowListener(new WindowAdapter() {
      public void windowClosing(WindowEvent e) {
	//stop the timer and exit
	timer.stop();
	System.exit(0);
      }});

    //GUI:
    label = new JLabel("Send frame #        ", JLabel.CENTER);
    getContentPane().add(label, BorderLayout.CENTER);
  }

  //------------------------------------
  //main
  //------------------------------------
  public static void main(String argv[]) throws Exception
  {
    //create a Server object
    Server theServer = new Server();

    //show GUI:
    theServer.pack();
    theServer.setVisible(true);

    //get RTSP socket port from the command line
    int RTSPport = Integer.parseInt(argv[0]);

    //Initiate TCP connection with the client for the RTSP session
    ServerSocket listenSocket = new ServerSocket(RTSPport);
    theServer.RTSPsocket = listenSocket.accept();
    listenSocket.close();

    //Get Client IP address
    theServer.ClientIPAddr = theServer.RTSPsocket.getInetAddress();

    //Initiate RTSPstate
    state = INIT;

    //Set input and output stream filters:
    RTSPBufferedReader = new BufferedReader(new InputStreamReader(theServer.RTSPsocket.getInputStream()) );
    RTSPBufferedWriter = new BufferedWriter(new OutputStreamWriter(theServer.RTSPsocket.getOutputStream()) );

    //Wait for the SETUP message from the client
    int request_type;
    boolean done = false;
    while(!done)
      {
	request_type = theServer.parse_RTSP_request(); //blocking

	if (request_type == SETUP)
	  {
	    done = true;

	    //update RTSP state
	    state = READY;
	    System.out.println("New RTSP state: READY");

	    //Send response
	    theServer.send_RTSP_response();

	    //init the VideoStream object:
	    theServer.video = new VideoStream(VideoFileName);

	    //init RTP socket
	    theServer.RTPsocket = new DatagramSocket();
	  }
      }

     //loop to handle RTSP requests
    while(true)
      {
	//parse the request
	request_type = theServer.parse_RTSP_request(); //blocking

	if ((request_type == PLAY) && (state == READY))
	  {
	    //send back response
	    theServer.send_RTSP_response();
	    //start timer
	    theServer.timer.start();
	    //update state
	    state = PLAYING;
	    System.out.println("New RTSP state: PLAYING");
	  }
	else if ((request_type == PAUSE) && (state == PLAYING))
	  {
	    //send back response
	    theServer.send_RTSP_response();
	    //stop timer
	    theServer.timer.stop();
	    //update state
	    state = READY;
	    System.out.println("New RTSP state: READY");
	  }
	else if (request_type == TEARDOWN)
	  {
	    //send back response
	    theServer.send_RTSP_response();
	    //stop timer
	    theServer.timer.stop();
	    //close sockets
	    theServer.RTSPsocket.close();
	    theServer.RTPsocket.close();

	    System.exit(0);
	  }
      }
  }


  //------------------------
  //Handler for timer
  //------------------------
  public void actionPerformed(ActionEvent e) {

    //if the current image nb is less than the length of the video
    if (imagenb < VIDEO_LENGTH)
      {
	//update current imagenb
	imagenb++;

	try {
	  //get next frame to send from the video, as well as its size
	  int image_length = video.getnextframe(buf);

	  //Builds an RTPpacket object containing the frame
	  RTPpacket rtp_packet = new RTPpacket(MJPEG_TYPE, imagenb, imagenb*FRAME_PERIOD, buf, image_length);

	  //get to total length of the full rtp packet to send
	  int packet_length = rtp_packet.getlength();

	  //retrieve the packet bitstream and store it in an array of bytes
	  byte[] packet_bits = new byte[packet_length];
	  rtp_packet.getpacket(packet_bits);

	  //send the packet as a DatagramPacket over the UDP socket
	  senddp = new DatagramPacket(packet_bits, packet_length, ClientIPAddr, RTP_dest_port);
	  RTPsocket.send(senddp);

	  //System.out.println("Send frame #"+imagenb);
	  //print the header bitstream
	  rtp_packet.printheader();

	  //update GUI
	  label.setText("Send frame #" + imagenb);
	}
	catch(Exception ex)
	  {
	    System.out.println("Exception caught: "+ex);
	    System.exit(0);
	  }
      }
    else
      {
	//if we have reached the end of the video file, stop the timer
	timer.stop();
      }
  }

  //------------------------------------
  //Parse RTSP Request
  //------------------------------------
  private int parse_RTSP_request()
  {
    int request_type = -1;
    try{
      //parse request line and extract the request_type:
      String RequestLine = RTSPBufferedReader.readLine();
      //System.out.println("RTSP Server - Received from Client:");
      System.out.println(RequestLine);

      StringTokenizer tokens = new StringTokenizer(RequestLine);
      String request_type_string = tokens.nextToken();

      //convert to request_type structure:
      if ((new String(request_type_string)).compareTo("SETUP") == 0)
	request_type = SETUP;
      else if ((new String(request_type_string)).compareTo("PLAY") == 0)
	request_type = PLAY;
      else if ((new String(request_type_string)).compareTo("PAUSE") == 0)
	request_type = PAUSE;
      else if ((new String(request_type_string)).compareTo("TEARDOWN") == 0)
	request_type = TEARDOWN;

      if (request_type == SETUP)
	{
	  //extract VideoFileName from RequestLine
	  VideoFileName = tokens.nextToken();
	}

      //parse the SeqNumLine and extract CSeq field
      String SeqNumLine = RTSPBufferedReader.readLine();
      System.out.println(SeqNumLine);
      tokens = new StringTokenizer(SeqNumLine);
      tokens.nextToken();
      RTSPSeqNb = Integer.parseInt(tokens.nextToken());

      //get LastLine
      String LastLine = RTSPBufferedReader.readLine();
      System.out.println(LastLine);

      if (request_type == SETUP)
	{
	  //extract RTP_dest_port from LastLine
	  tokens = new StringTokenizer(LastLine);
	  for (int i=0; i<3; i++)
	    tokens.nextToken(); //skip unused stuff
	  RTP_dest_port = Integer.parseInt(tokens.nextToken());
	}
      //else LastLine will be the SessionId line ... do not check for now.
    }
    catch(Exception ex)
      {
	System.out.println("Exception caught: "+ex);
	System.exit(0);
      }
    return(request_type);
  }

  //------------------------------------
  //Send RTSP Response
  //------------------------------------
  private void send_RTSP_response()
  {
    try{
      RTSPBufferedWriter.write("RTSP/1.0 200 OK"+CRLF);
      RTSPBufferedWriter.write("CSeq: "+RTSPSeqNb+CRLF);
      RTSPBufferedWriter.write("Session: "+RTSP_ID+CRLF);
      RTSPBufferedWriter.flush();
      //System.out.println("RTSP Server - Sent response to Client.");
    }
    catch(Exception ex)
      {
	System.out.println("Exception caught: "+ex);
	System.exit(0);
      }
  }
}'''
