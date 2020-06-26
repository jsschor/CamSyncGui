from ttk import *
import tkinter as tk
from tkinter import *
import cv2
from PIL import Image, ImageTk
import os
import numpy as np
import picamera
from picamera.array import PiRGBArray
import imutils.imutils as imutils
from imutils.imutils.video import VideoStream
import time
import RPi.GPIO as GPIO

cap = VideoStream(src=0).start()
# cap2 = VideoStream(usePiCamera=True).start()
cap2 = VideoStream(src=3).start()
time.sleep(2.0)
startTime = time.time()
lineHolder = list()
global lineHolder2
lineHolder2 = list()
graphCheck = -1
global graphCheck2
graphCheck2 = -1
frac=0
minTime=0

inputPin1 = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(inputPin1, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(inputPin1, GPIO.RISING,
                          callback = lambda x: cbf(inputPin1,frac,minTime))

def cbf(gpio,frac,minTime):
    global graphCheck2
    global lineHolder2
    if GPIO.input(inputPin1):
        lineHolder2.append(frac)
        if graphCheck2 == -1:
            graphCheck2 = minTime

while True:
    counter = 0
    h = 240
    w = 320
    extraSpace = 100
    lineBarrier = 60
    output = np.zeros((h+extraSpace,w*2,3),'uint8')
    timeStamps = np.zeros((2,1));
    for (stream,name) in zip((cap,cap2),("Webcam","PiCam")):
        frame = stream.read()
        ts = time.time()-startTime
        frame = imutils.resize(frame,width=w,height=h)
        output[0:h,w*counter:w*(counter+1)] = frame
        timeStamps[counter] = ts
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
            (0,0,255),1)
    elif graphCheck2 != minTime and graphCheck2 != -1:
        graphCheck2 = -1
        lineHolder2 = list()
        
    cv2.imshow('comboImg',output)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("1"):
        lineHolder.append(frac)
        if graphCheck == -1:
            graphCheck = minTime
    
#     if pi_GPIO.read(inputPin1):
#         lineHolder2.append(frac)
#         if graphCheck2 == -1:
#             graphCheck2 = minTime
        
cv2.destroyAllWindows()
cap.stop()
cap2.stop()

