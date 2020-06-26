from ttk import *
import tkinter as tk
from tkinter import *
from tkinter import simpledialog
import cv2
from PIL import Image, ImageTk
import os
import numpy as np
import picamera
from picamera.array import PiRGBArray
import imutils.imutils as imutils
from imutils.imutils.video import VideoStream
import time
import pigpio
from datetime import datetime
import csv
from itertools import zip_longest

global graphCheck2
global lineHolder2
global inputPin1
global minTime
global startTime
global timeLength
global TTL1ts

cap = VideoStream(src=0).start()
# cap2 = VideoStream(usePiCamera=True).start()
cap2 = VideoStream(src=2).start()
time.sleep(2.0)
startTime = time.time()
lineHolder = list()
lineHolder2 = list()
graphCheck = -1
graphCheck2 = -1
frac=0
minTime=0

GPIO = pigpio.pi()
inputPin1 = 24
GPIO.set_mode(inputPin1,pigpio.INPUT)
GPIO.set_pull_up_down(inputPin1,pigpio.PUD_UP)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
writer = None
writer2 = None
tsFile = None

cam1ts = list()
cam2ts = list()
keyboard1ts = list()
TTL1ts = list()

global stimCount
stimCount = 1

def cbf(g,l,t):
    global graphCheck2
    global lineHolder2
    global inputPin1
    global minTime
    global startTime
    global timeLength
    global stimCount
    global TTL1ts
    
    print(stimCount)
    stimCount+=1
    
    ts = time.time()-startTime
    realDiv = ts/timeLength
    frac = realDiv-minTime/timeLength
    TTL1ts.append(ts)
    lineHolder2.append(frac)
    if graphCheck2 == -1:
        graphCheck2 = minTime
            
GPIO.callback(inputPin1, pigpio.RISING_EDGE,cbf)

#Allow for user to put in experiment name
askWindow = tk.Tk()
exptName = simpledialog.askstring("Expt Name","Enter an experiment name:",parent=askWindow)
askWindow.destroy()

while True:
    counter = 0
    h = 240
    w = 320
    extraSpace = 100
    lineBarrier = 60
    output = np.zeros((h+extraSpace,w*2,3),'uint8')
    timeStamps = np.zeros((2,1));
    
    if writer is None:
        now = datetime.now()
        saveName = now.strftime("%y%m%d-%H%M%S")
        saveName = "{}-{}".format(exptName,saveName)
        os.mkdir("/home/pi/CamSyncVids/{}".format(saveName))
        writer = cv2.VideoWriter("/home/pi/CamSyncVids/{}/{}_Cam1.avi".format(saveName,saveName),fourcc,20,(w,h),True)
        writer2 = cv2.VideoWriter("/home/pi/CamSyncVids/{}/{}_Cam2.avi".format(saveName,saveName),fourcc,20,(w,h),True)
        tsFile = open("/home/pi/CamSyncVids/{}/{}_timestamps.csv".format(saveName,saveName),'w')
        tsFileWriter = csv.writer(tsFile)
        tsFileWriter.writerow(["Cam1", "Cam2", "Keyboard1", "TTL1"])
    for (stream,name) in zip((cap,cap2),("Webcam","PiCam")):
        frame = stream.read()
        ts = time.time()-startTime
        frame = imutils.resize(frame,width=w,height=h)
        output[0:h,w*counter:w*(counter+1)] = frame
        timeStamps[counter] = ts
        if counter==0:
            cam1ts.append(ts)
            writer.write(frame)
        elif counter==1:
            cam2ts.append(ts)
            writer2.write(frame)
        counter +=1
    cv2.putText(output,'{}'.format(timeStamps[0]),(10,h-10),
                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,0,255),1)
    cv2.putText(output,'{}'.format(timeStamps[1]),(w+10,h-10),
                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,0,255),1)
    
    timeLength = 5
    minTime = np.floor(ts/timeLength)*timeLength
    maxTime = np.ceil(ts/timeLength)*timeLength
    realDiv = ts/timeLength
    frac = realDiv-minTime/timeLength
    cv2.putText(output,'{}'.format(minTime),(10,output.shape[0]-10),
                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
    cv2.putText(output,'{}'.format(maxTime),(2*w-50,output.shape[0]-10),
                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
    cv2.putText(output,'M1',(10,h + int(3*extraSpace/10)),
                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
    cv2.putText(output,'I1',(10,h + int(6*extraSpace/10)),
                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
    cv2.line(output,(int((2*w-2*lineBarrier)*frac+lineBarrier),h  + 10),
            (int((2*w-2*lineBarrier)*frac+lineBarrier),h + extraSpace -10),
            (255,255,255),3)
    if graphCheck == minTime:
        for lines in lineHolder:
            cv2.line(output,(int((2*w-2*lineBarrier)*lines+lineBarrier),h+20),
            (int((2*w-2*lineBarrier)*lines+lineBarrier),h+20+int(2*extraSpace/10)),
            (0,0,255),1)
    elif graphCheck != minTime and graphCheck != -1:
        graphCheck = -1
        lineHolder = list()
        
    if graphCheck2 == minTime:
        for lines in lineHolder2:
            cv2.line(output,(int((2*w-2*lineBarrier)*lines+lineBarrier),h+int(2*extraSpace/5)+10),
            (int((2*w-2*lineBarrier)*lines+lineBarrier),h+int(2*extraSpace/5)+10+int(2*extraSpace/10)),
            (0,255,0),1)
    elif graphCheck2 != minTime and graphCheck2 != -1:
        graphCheck2 = -1
        lineHolder2 = list()
        
    cv2.imshow('comboImg',output)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("1"):
        keyboard1ts.append(ts)
        lineHolder.append(frac)
        if graphCheck == -1:
            graphCheck = minTime
    
#     if pi_GPIO.read(inputPin1):
#         lineHolder2.append(frac)
#         if graphCheck2 == -1:
#             graphCheck2 = minTime
for row in zip_longest(cam1ts,cam2ts,keyboard1ts,TTL1ts):
    tsFileWriter.writerow(row)
tsFile.flush()
tsFile.close()
cv2.destroyAllWindows()
cap.stop()
cap2.stop()
writer.release()
writer2.release()

