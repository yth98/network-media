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
import numpy
import socket
import random
import _thread
import tkinter as tk
from enum import Enum
from PIL import Image, ImageTk
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
    global state, CSeq, client_p, server_p, session, t
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
    global state
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
    global state, client_p, w, e, buffer_img
    r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    r.bind(("", client_p))
    r.settimeout(5)
    while(True):
        if(state!=C_.PLAYING): # no segment to recv
            continue
        try:
            buffer_img, adr = r.recvfrom(65536) # limitation is 64KB
            if(adr[1]!=server_p): continue # ignore messages from wrong port
            #print("Recv",len(buffer_img),"bytes")
        except socket.timeout:
            print("RTP Timeout.")
            state=C_.READY

def vid_display():
    global state, buffer_img
    while(state==C_.PLAYING):
        try:
            global disp
            disp = cv2.resize(cv2.imdecode(numpy.fromstring(buffer_img, numpy.uint8),cv2.IMREAD_COLOR), (wid,hei))
            cv2.imshow("RTSP Client Player", disp)
        except cv2.error:
            print("Bad frame.")
            continue
        cv2.waitKey(50)
    if(state==C_.INIT): cv2.imshow("RTSP Client Player", bk)
    else: cv2.imshow("RTSP Client Player", disp) # state==C_.READY

'''parallel = Process(target=rtp_rec)
parallel.start()
parallel.join()
print(parallel.exitcode)'''

# turn on the webcam or open test-file
cap = cv2.VideoCapture("i_test.mp4")
buffer_img = b''

# generate GUI
master = tk.Tk()
master.title("RTSP Client Control Panel")
master.resizable(False,False)

wid, hei = 480, 360
disp = bk = numpy.zeros((hei,wid,3), numpy.uint8)
cv2.namedWindow("RTSP Client Player")
cv2.imshow("RTSP Client Player", bk)

b = []
for i in range(4):
    tx={0:"SETUP",1:"PLAY",2:"PAUSE",3:"TEARDOWN"}.get(i)
    cmd={0:c_setup,1:c_play,2:c_pause,3:c_down}.get(i)
    b.append(tk.Button(master,text=tx,command=cmd,width=10,height=2))
    b[i].grid(row=0, column=i, sticky=tk.W+tk.E)

e = tk.Entry(master)
e.grid(row=1, column=0, columnspan=4, sticky=tk.W+tk.E)
e.bind("<Return>", set_param)

_thread.start_new_thread(rtp_rec,())

master.mainloop()

'''
Client.java

/* ------------------
   Client
   usage: java Client [Server hostname] [Server RTSP listening port] [Video file requested]
   ---------------------- */

import java.io.*;
import java.net.*;
import java.util.*;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;
import javax.swing.Timer;

public class Client{

  //GUI
  //----
  JFrame f = new JFrame("Client");
  JButton setupButton = new JButton("Setup");
  JButton playButton = new JButton("Play");
  JButton pauseButton = new JButton("Pause");
  JButton tearButton = new JButton("Teardown");
  JPanel mainPanel = new JPanel();
  JPanel buttonPanel = new JPanel();
  JLabel iconLabel = new JLabel();
  ImageIcon icon;


  //RTP variables:
  //----------------
  DatagramPacket rcvdp; //UDP packet received from the server
  DatagramSocket RTPsocket; //socket to be used to send and receive UDP packets
  static int RTP_RCV_PORT = 25000; //port where the client will receive the RTP packets
  
  Timer timer; //timer used to receive data from the UDP socket
  byte[] buf; //buffer used to store data received from the server 
 
  //RTSP variables
  //----------------
  //rtsp states 
  final static int INIT = 0;
  final static int READY = 1;
  final static int PLAYING = 2;
  static int state; //RTSP state == INIT or READY or PLAYING
  Socket RTSPsocket; //socket used to send/receive RTSP messages
  //input and output stream filters
  static BufferedReader RTSPBufferedReader;
  static BufferedWriter RTSPBufferedWriter;
  static String VideoFileName; //video file to request to the server
  int RTSPSeqNb = 0; //Sequence number of RTSP messages within the session
  int RTSPid = 0; //ID of the RTSP session (given by the RTSP Server)

  final static String CRLF = "\r\n";

  //Video constants:
  //------------------
  static int MJPEG_TYPE = 26; //RTP payload type for MJPEG video
 
  //--------------------------
  //Constructor
  //--------------------------
  public Client() {

    //build GUI
    //--------------------------
 
    //Frame
    f.addWindowListener(new WindowAdapter() {
       public void windowClosing(WindowEvent e) {
	 System.exit(0);
       }
    });

    //Buttons
    buttonPanel.setLayout(new GridLayout(1,0));
    buttonPanel.add(setupButton);
    buttonPanel.add(playButton);
    buttonPanel.add(pauseButton);
    buttonPanel.add(tearButton);
    setupButton.addActionListener(new setupButtonListener());
    playButton.addActionListener(new playButtonListener());
    pauseButton.addActionListener(new pauseButtonListener());
    tearButton.addActionListener(new tearButtonListener());

    //Image display label
    iconLabel.setIcon(null);
    
    //frame layout
    mainPanel.setLayout(null);
    mainPanel.add(iconLabel);
    mainPanel.add(buttonPanel);
    iconLabel.setBounds(0,0,380,280);
    buttonPanel.setBounds(0,280,380,50);

    f.getContentPane().add(mainPanel, BorderLayout.CENTER);
    f.setSize(new Dimension(390,370));
    f.setVisible(true);

    //init timer
    //--------------------------
    timer = new Timer(20, new timerListener());
    timer.setInitialDelay(0);
    timer.setCoalesce(true);

    //allocate enough memory for the buffer used to receive data from the server
    buf = new byte[15000];    
  }

  //------------------------------------
  //main
  //------------------------------------
  public static void main(String argv[]) throws Exception
  {
    //Create a Client object
    Client theClient = new Client();
    
    //get server RTSP port and IP address from the command line
    //------------------
    int RTSP_server_port = Integer.parseInt(argv[1]);
    String ServerHost = argv[0];
    InetAddress ServerIPAddr = InetAddress.getByName(ServerHost);

    //get video filename to request:
    VideoFileName = argv[2];

    //Establish a TCP connection with the server to exchange RTSP messages
    //------------------
    theClient.RTSPsocket = new Socket(ServerIPAddr, RTSP_server_port);

    //Set input and output stream filters:
    RTSPBufferedReader = new BufferedReader(new InputStreamReader(theClient.RTSPsocket.getInputStream()) );
    RTSPBufferedWriter = new BufferedWriter(new OutputStreamWriter(theClient.RTSPsocket.getOutputStream()) );

    //init RTSP state:
    state = INIT;
  }


  //------------------------------------
  //Handler for buttons
  //------------------------------------

  //.............
  //TO COMPLETE
  //.............

  //Handler for Setup button
  //-----------------------
  class setupButtonListener implements ActionListener{
    public void actionPerformed(ActionEvent e){

      //System.out.println("Setup Button pressed !");      

      if (state == INIT) 
	{
	  //Init non-blocking RTPsocket that will be used to receive data
	  try{
	    //construct a new DatagramSocket to receive RTP packets from the server, on port RTP_RCV_PORT
	    //RTPsocket = ...

	    //set TimeOut value of the socket to 5msec.
	    //....

	  }
	  catch (SocketException se)
	    {
	      System.out.println("Socket exception: "+se);
	      System.exit(0);
	    }

	  //init RTSP sequence number
	  RTSPSeqNb = 1;
	 
	  //Send SETUP message to the server
	  send_RTSP_request("SETUP");

	  //Wait for the response 
	  if (parse_server_response() != 200)
	    System.out.println("Invalid Server Response");
	  else 
	    {
	      //change RTSP state and print new state 
	      //state = ....
	      //System.out.println("New RTSP state: ....");
	    }
	}//else if state != INIT then do nothing
    }
  }
  
  //Handler for Play button
  //-----------------------
  class playButtonListener implements ActionListener {
    public void actionPerformed(ActionEvent e){

      //System.out.println("Play Button pressed !"); 

      if (state == READY) 
	{
	  //increase RTSP sequence number
	  //.....


	  //Send PLAY message to the server
	  send_RTSP_request("PLAY");

	  //Wait for the response 
	  if (parse_server_response() != 200)
		  System.out.println("Invalid Server Response");
	  else 
	    {
	      //change RTSP state and print out new state
	      //.....
	      // System.out.println("New RTSP state: ...")

	      //start the timer
	      timer.start();
	    }
	}//else if state != READY then do nothing
    }
  }


  //Handler for Pause button
  //-----------------------
  class pauseButtonListener implements ActionListener {
    public void actionPerformed(ActionEvent e){

      //System.out.println("Pause Button pressed !");   

      if (state == PLAYING) 
	{
	  //increase RTSP sequence number
	  //........

	  //Send PAUSE message to the server
	  send_RTSP_request("PAUSE");
	
	  //Wait for the response 
	 if (parse_server_response() != 200)
		  System.out.println("Invalid Server Response");
	  else 
	    {
	      //change RTSP state and print out new state
	      //........
	      //System.out.println("New RTSP state: ...");
	      
	      //stop the timer
	      timer.stop();
	    }
	}
      //else if state != PLAYING then do nothing
    }
  }

  //Handler for Teardown button
  //-----------------------
  class tearButtonListener implements ActionListener {
    public void actionPerformed(ActionEvent e){

      //System.out.println("Teardown Button pressed !");  

      //increase RTSP sequence number
      // ..........
      

      //Send TEARDOWN message to the server
      send_RTSP_request("TEARDOWN");

      //Wait for the response 
      if (parse_server_response() != 200)
	System.out.println("Invalid Server Response");
      else 
	{     
	  //change RTSP state and print out new state
	  //........
	  //System.out.println("New RTSP state: ...");

	  //stop the timer
	  timer.stop();

	  //exit
	  System.exit(0);
	}
    }
  }


  //------------------------------------
  //Handler for timer
  //------------------------------------
  
  class timerListener implements ActionListener {
    public void actionPerformed(ActionEvent e) {
      
      //Construct a DatagramPacket to receive data from the UDP socket
      rcvdp = new DatagramPacket(buf, buf.length);

      try{
	//receive the DP from the socket:
	RTPsocket.receive(rcvdp);
	  
	//create an RTPpacket object from the DP
	RTPpacket rtp_packet = new RTPpacket(rcvdp.getData(), rcvdp.getLength());

	//print important header fields of the RTP packet received: 
	System.out.println("Got RTP packet with SeqNum # "+rtp_packet.getsequencenumber()+" TimeStamp "+rtp_packet.gettimestamp()+" ms, of type "+rtp_packet.getpayloadtype());
	
	//print header bitstream:
	rtp_packet.printheader();

	//get the payload bitstream from the RTPpacket object
	int payload_length = rtp_packet.getpayload_length();
	byte [] payload = new byte[payload_length];
	rtp_packet.getpayload(payload);

	//get an Image object from the payload bitstream
	Toolkit toolkit = Toolkit.getDefaultToolkit();
	Image image = toolkit.createImage(payload, 0, payload_length);
	
	//display the image as an ImageIcon object
	icon = new ImageIcon(image);
	iconLabel.setIcon(icon);
      }
      catch (InterruptedIOException iioe){
	//System.out.println("Nothing to read");
      }
      catch (IOException ioe) {
	System.out.println("Exception caught: "+ioe);
      }
    }
  }

  //------------------------------------
  //Parse Server Response
  //------------------------------------
  private int parse_server_response() 
  {
    int reply_code = 0;

    try{
      //parse status line and extract the reply_code:
      String StatusLine = RTSPBufferedReader.readLine();
      //System.out.println("RTSP Client - Received from Server:");
      System.out.println(StatusLine);
    
      StringTokenizer tokens = new StringTokenizer(StatusLine);
      tokens.nextToken(); //skip over the RTSP version
      reply_code = Integer.parseInt(tokens.nextToken());
      
      //if reply code is OK get and print the 2 other lines
      if (reply_code == 200)
	{
	  String SeqNumLine = RTSPBufferedReader.readLine();
	  System.out.println(SeqNumLine);
	  
	  String SessionLine = RTSPBufferedReader.readLine();
	  System.out.println(SessionLine);
	
	  //if state == INIT gets the Session Id from the SessionLine
	  tokens = new StringTokenizer(SessionLine);
	  tokens.nextToken(); //skip over the Session:
	  RTSPid = Integer.parseInt(tokens.nextToken());
	}
    }
    catch(Exception ex)
      {
	System.out.println("Exception caught: "+ex);
	System.exit(0);
      }
    
    return(reply_code);
  }

  //------------------------------------
  //Send RTSP Request
  //------------------------------------

  //.............
  //TO COMPLETE
  //.............
  
  private void send_RTSP_request(String request_type)
  {
    try{
      //Use the RTSPBufferedWriter to write to the RTSP socket

      //write the request line:
      //RTSPBufferedWriter.write(...);

      //write the CSeq line: 
      //......

      //check if request_type is equal to "SETUP" and in this case write the Transport: line advertising to the server the port used to receive the RTP packets RTP_RCV_PORT
      //if ....
      //otherwise, write the Session line from the RTSPid field
      //else ....

      RTSPBufferedWriter.flush();
    }
    catch(Exception ex)
      {
	System.out.println("Exception caught: "+ex);
	System.exit(0);
      }
  }

}//end of Class Client

'''
