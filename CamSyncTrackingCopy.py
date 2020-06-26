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
import math
import tkSimpleDialog

global graphCheck2
global lineHolder2
global inputPin1
global minTime
global startTime
global timeLength
global TTL1ts
global angleAcc
global graphCheck3
global lineHolder3
global inputPin2
global TTL2ts
global firstPoint
global bkgdOutput
global bkgdOutputSave
global ix
global ix2
global iy
global iy2

startTime = time.time()
lineHolder = list()
lineHolder2 = list()
lineHolder3 = list()
graphCheck = -1
graphCheck2 = -1
graphCheck3 = -1
frac=0
minTime=0
buttonAlpha = .5
swapVids = 0
showPulseCounts = 0

GPIO = pigpio.pi()
inputPin1 = 24
GPIO.set_mode(inputPin1,pigpio.INPUT)
GPIO.set_pull_up_down(inputPin1,pigpio.PUD_UP)
inputPin2 = 25
GPIO.set_mode(inputPin2,pigpio.INPUT)
GPIO.set_pull_up_down(inputPin2,pigpio.PUD_UP)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
writerList = None
tsFile = None
bkgdList = None
twoCam=1
ROINum = 2
ROIList = list()
ROINameList = list()
ROIShowCheck = list()
ROIStatList = list()

camTsList = list()
camCtrXList = list()
camCtrYList = list()
camVelList = list()
camRotList = list()
keyboard1ts = list()
TTL1ts = list()
TTL2ts = list()
camList = list()

#Make new class for initial dialog box
class StartDialog(tkSimpleDialog.Dialog):
    
    def body(self,master):
        Label(master,text="Enter an experiment name:").grid(row=0,sticky=W)
        Label(master,text="Enter experiment condition:").grid(row=1,sticky=W)
        Label(master,text="Enter sync'd file name:").grid(row=2,sticky=W)
        Label(master,text="Enter recording time in secs (leave blank for inf):").grid(row=3,sticky=W)
        
        self.e1 = Entry(master)
        self.e2 = Entry(master)
        self.e3 = Entry(master)
        self.e4 = Entry(master)
        
        self.e1.grid(row=0,column=1)
        self.e2.grid(row=1,column=1)
        self.e3.grid(row=2,column=1)
        self.e4.grid(row=3,column=1)
        
        self.cbState = IntVar()
        self.cb = Checkbutton(master,text="Enable Tracking?",variable=self.cbState)
        self.cb.grid(row=4,columnspan=2,sticky=W)
        self.cbState.set(1)
        
        self.cbState2 = IntVar()
        self.cb2 = Checkbutton(master,text="Enable Two Cameras?",variable=self.cbState2)
        self.cb2.grid(row=5,columnspan=2,sticky=W)
        self.cbState2.set(1)
        
        return self.e1
    
    def apply(self):
        exptName = self.e1.get()
        condit = self.e2.get()
        syncFile = self.e3.get()
        shutoffTime = self.e4.get()
        trackingToggle = self.cbState.get()
        twoCam = self.cbState2.get()
        self.result = exptName,condit,syncFile,shutoffTime,trackingToggle,twoCam

#Allow for user to put in experiment name
askWindow = tk.Tk()
d = StartDialog(askWindow)
[exptName,condit,syncFile,shutoffTime,trackingToggle,twoCam] = d.result
if len(shutoffTime)==0:
    shutoffTime = np.inf
else:
    shutoffTime = float(shutoffTime)
askWindow.destroy()

h = 240
w = 320
if twoCam:
    cap = VideoStream(src=2,resolution=(w,h)).start()
    # cap2 = VideoStream(usePiCamera=True).start()
    cap2 = VideoStream(src=0,resolution=(w,h)).start()
    camList = [cap,cap2]
    camTsList = [list(),list()]
    ROIList = [list(),list()]
    ROINameList = [list(),list()]
    ROIStatList = [list(),list()]
    ROIShowCheck = [0,0]
    camCtrXList = [list(),list()]
    camCtrYList = [list(),list()]
    camVelList = [list(),list()]
    camRotList = [list(),list()]
    anglePrev = [list(),list()]
else:
    cap = VideoStream(src=2,resolution=(w*2,h*2)).start()
    camList = [cap]
    camTsList = [list()]
    ROIList = [list()]
    ROINameList = [list()]
    ROIStatList = [list()]
    ROIShowCheck = [0]
    camCtrXList = [list()]
    camCtrYList = [list()]
    camVelList = [list()]
    camRotList = [list()]
    anglePrev = [list()]
time.sleep(2.0)

timeLength = 30
bkgd = np.zeros((h,w,2),'uint8')
diffHolder = np.zeros((h,w*2),'uint8')
lowThresh = None
highThresh = None
knownDist = [None]
firstPoint = None
(ROIx1,ROIy1,ROIw1,ROIh1) = (None,None,None,None)
(ROIx2,ROIy2,ROIw2,ROIh2) = (None,None,None,None)
ix = 0
iy = 0
ix2 = 0
iy2 = 0

angleAcc = 0
angle = None
global stimCount
global stimCount2
stimCount = 1
stimCount2 = 1

def cbf(g,l,t):
    global graphCheck2
    global lineHolder2
    global inputPin1
    global minTime
    global startTime
    global timeLength
    global stimCount
    global TTL1ts
    
#     print(stimCount)
    stimCount+=1
    
    ts = time.time()-startTime
    realDiv = ts/timeLength
    frac = realDiv-minTime/timeLength
    TTL1ts.append(ts)
    lineHolder2.append(frac)
    if graphCheck2 == -1:
        graphCheck2 = minTime
            
GPIO.callback(inputPin1, pigpio.RISING_EDGE,cbf)

def cbf2(g,l,t):
    global graphCheck3
    global lineHolder3
    global inputPin2
    global minTime
    global startTime
    global timeLength
    global stimCount2
    global TTL2ts
    
#     print(stimCount2)
    stimCount2+=1
    
    ts = time.time()-startTime
    realDiv = ts/timeLength
    frac = realDiv-minTime/timeLength
    TTL2ts.append(ts)
    lineHolder3.append(frac)
    if graphCheck3 == -1:
        graphCheck3 = minTime

GPIO.callback(inputPin2, pigpio.RISING_EDGE,cbf2)

#Code for drawing line
def draw(event,x,y,flags,params):
    global ix,iy,ix2,iy2,firstPoint
    if event==cv2.EVENT_LBUTTONDOWN and firstPoint is None:
        ix = x
        iy = y
        ix2 = x
        iy2 = y
        firstPoint = 1
    if event==cv2.EVENT_MOUSEMOVE and firstPoint==1:
        ix2 = x
        iy2 = y
    if event==cv2.EVENT_LBUTTONUP and firstPoint==1:
        firstPoint = None
        
#Code for bkgdChooseButton(s)
def buttonHandler(event,x,y,flags,params):
    global camList,w,h,bkgdOutput
    if event==cv2.EVENT_LBUTTONDOWN and x>bkgdOutput.shape[1]-25:
        if y>h-25 and y<h:
            camTemp = camList[0]
            camList[0] = camList[-1]
            camList[-1] = camTemp
            
#Code for main gui button(s)
def buttonHandler2(event,x,y,flags,params):
    global swapVids,output,w,h,timeLength,twoCam
    global ROIList,ROIStatList,ROIShowCheck,showPulseCounts
    global lineBarrier
    if event==cv2.EVENT_LBUTTONDOWN and x>output.shape[1]-25:
        if y>h-25 and y<h:
            swapVids = not swapVids
        elif y>h+10 and y<h+35:
            print('up')
        
        elif y>h+50 and y<h+75:
            print('down')
    if event==cv2.EVENT_LBUTTONDOWN and y<h:
        if x<output.shape[1]//2:
            for i,ROIs in enumerate(ROIList[0]):
                (ROIxuse,ROIyuse,ROIwuse,ROIhuse) = ROIs
                if x>ROIxuse and x<ROIxuse+ROIwuse and y>ROIyuse and y<ROIyuse+ROIhuse:
                    #Temp save current value
                    tempStatVal = not ROIStatList[0][i]
                    #Reset everything to 0
                    ROIStatList[0] = [0] * (len(ROIStatList[0]))
                    #Insert temp value
                    ROIStatList[0][i] = tempStatVal
        elif x>output.shape[1]//2 and twoCam:
            for i,ROIs in enumerate(ROIList[1]):
                (ROIxuse,ROIyuse,ROIwuse,ROIhuse) = ROIs
                if x>ROIxuse+w and x<ROIxuse+ROIwuse+w and y>ROIyuse and y<ROIyuse+ROIhuse:
                    tempStatVal = not ROIStatList[1][i]
                    ROIStatList[1] = [0] * (len(ROIStatList[1]))
                    ROIStatList[1][i] = tempStatVal
    if event==cv2.EVENT_LBUTTONDBLCLK and y>output.shape[0]-20:
        if x<output.shape[1]//2:
            if timeLength>1:
                timeLength = timeLength/2
        elif x>output.shape[1]//2:
            if timeLength<300:
                timeLength = timeLength*2
    if event==cv2.EVENT_LBUTTONDBLCLK and x<lineBarrier and y<output.shape[0]-20 and y>h:
        showPulseCounts = not showPulseCounts
    if event==cv2.EVENT_LBUTTONDBLCLK and y<h:
        if x<output.shape[1]//2:
            ROIShowCheck[0] = not ROIShowCheck[0]
        elif x>output.shape[1]//2 and twoCam:
            ROIShowCheck[1] = not ROIShowCheck[1]
        

#Do nothing for sliders
def nothing(x):
    pass

# Function for determining rotation
def rotCounter(angleNow,anglePrev):
    global angleAcc
    
    rotatFull = 0
    angleDiff = (angleNow-anglePrev)
    if angleDiff>(np.pi/2):
        angleDiff -= np.pi
    elif angleDiff<(-np.pi/2):
        angleDiff += np.pi
    
    if angleDiff>0:
        direction = "Right"
    elif angleDiff<0:
        direction = "Left"
    else:
        direction = "Straight"
    
    angleAcc += angleDiff
    if angleAcc > np.pi:
        rotatFull = 1
        angleAcc = 0
    elif angleAcc< -np.pi:
        rotatFull = -1
        angleAcc = 0
#     print(angleAcc)
    return rotatFull

startTime = time.time()

while True:
    counter = 0
    extraSpace = 110
    lineBarrier = 60
    output = np.zeros((h+extraSpace,w*2,3),'uint8')
    timeStamps = np.zeros((2,1));
    
    if not np.count_nonzero(bkgd) and trackingToggle:
        cv2.namedWindow('selectBackground')
        cv2.setMouseCallback('selectBackground',buttonHandler)
        bkgdOutput = np.zeros((h+extraSpace,w*2,3),'uint8')
        counter = 0
        for stream in camList:
            frame = stream.read()
            frame = imutils.resize(frame,width=w,height=h)
            bkgdOutput[0:h,w*counter:w*(counter+1)] = frame
            counter +=1
            
        cv2.putText(bkgdOutput,'Press the "1" key to take a background image',
                    (40,h + int(6*extraSpace/10)),
                        cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
        overlay = bkgdOutput.copy()
        bkgdOutputCopy = bkgdOutput.copy()
        cv2.rectangle(overlay,(2*w-25,h-25),
                              (2*w,h-1),
                              (150,150,150),
                              -1)
        cv2.rectangle(overlay,(2*w-25,h-25),
                              (2*w,h-1),
                              (255,255,255),
                              1)
        cv2.putText(overlay,'< >',(2*w-20,h-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.25,(255,255,255),2)
        cv2.addWeighted(overlay,buttonAlpha,bkgdOutputCopy,1-buttonAlpha,0,bkgdOutputCopy)
        cv2.imshow('selectBackground',bkgdOutputCopy)
    
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("1"):
            cv2.setMouseCallback('selectBackground',lambda *args:None)
            bkgd[0:h,0:w,0] = cv2.cvtColor(bkgdOutput[0:h,0:w],cv2.COLOR_BGR2GRAY)
            bkgd[0:h,0:w,0] = cv2.GaussianBlur(bkgd[0:h,0:w,0],(5,5),0)
            bkgd[0:h,0:w,1] = cv2.cvtColor(bkgdOutput[0:h,w:2*w],cv2.COLOR_BGR2GRAY)
            bkgd[0:h,0:w,1] = cv2.GaussianBlur(bkgd[0:h,0:w,1],(5,5),0)
            bkgdOutput[h:h+extraSpace,0:w*2,0:3] = np.zeros((extraSpace,w*2,3),'uint8')
            bkgdOutputSave = np.copy(bkgdOutput)
            bkgdList = list()
            for i in range(len(camList)):
                bkgdList.append(np.copy(bkgdOutput[0:h,i*w:(i+1)*w,:]))
            for i in range(ROINum):
                cv2.putText(bkgdOutput,'Select ROI {} then press "space"'.format(i+1),
                        (40,h + int(6*extraSpace/10)),
                            cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
                outOfBounds = True
                while outOfBounds:
                    (ROIx,ROIy,ROIw,ROIh) = cv2.selectROI('selectBackground',bkgdOutput,False,False)
                    if ROIx+ROIw<w and ROIy+ROIh<h:
                        ROIList[0].append([ROIx,ROIy,ROIw,ROIh])
                        ROIStatList[0].append(0)
                        camCtrXList[0].append(list())
                        camCtrYList[0].append(list())
                        camVelList[0].append(list())
                        camRotList[0].append(list())
                        anglePrev[0].append(None)
                        nameROIWindow = tk.Tk()
                        ROIName = simpledialog.askstring("ROI{}".format(i+1),
                                                         "Enter an ROI name",
                                                         parent=nameROIWindow,
                                                         initialvalue="ROI{}".format(i+1))
                        nameROIWindow.destroy()
                        ROINameList[0].append(ROIName)
                        outOfBounds = False
                        
                    elif ROIx>w and twoCam and ROIy+ROIh<h:
                        ROIList[1].append([ROIx-w,ROIy,ROIw,ROIh])
                        ROIStatList[1].append(0)
                        camCtrXList[1].append(list())
                        camCtrYList[1].append(list())
                        camVelList[1].append(list())
                        camRotList[1].append(list())
                        anglePrev[1].append(None)
                        nameROIWindow = tk.Tk()
                        ROIName = simpledialog.askstring("ROI{}".format(i+1),
                                                         "Enter an ROI name",
                                                         parent=nameROIWindow,
                                                         initialvalue="ROI{}".format(i+1))
                        nameROIWindow.destroy()
                        ROINameList[1].append(ROIName)
                        outOfBounds = False
                    else:
                        bkgdOutput[h:h+extraSpace,0:w*2,0:3] = np.zeros((extraSpace,w*2,3),'uint8')
                        cv2.putText(bkgdOutput,'Out of bounds.',
                        (40,h + int(6*extraSpace/10)),
                            cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
                        cv2.putText(bkgdOutput,'Reselect ROI {} then press "space"'.format(i+1),
                        (40,h + int(8*extraSpace/10)),
                            cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
                bkgdOutput[h:h+extraSpace,0:w*2,0:3] = np.zeros((extraSpace,w*2,3),'uint8')
                
            bkgdOutput = np.copy(bkgdOutputSave)
            bkgdOutput[h:h+extraSpace,0:w*2,0:3] = np.zeros((extraSpace,w*2,3),'uint8')
            cv2.putText(bkgdOutput,'Draw known distance then press "space"',
                    (40,h + int(6*extraSpace/10)),
                        cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
            bkgdOutputSave = np.copy(bkgdOutput)
            cv2.setMouseCallback('selectBackground',draw)
            while knownDist[0] is None:
                bkgdOutput = np.copy(bkgdOutputSave)
                cv2.line(bkgdOutput,pt1=(ix,iy),pt2=(ix2,iy2),
                 color=(255,255,255),
                 thickness=2)
                cv2.imshow('selectBackground',bkgdOutput)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord(" "):
                    a = np.array((ix,iy))
                    b = np.array((ix2,iy2))
                    knownDist = [np.linalg.norm(a-b)]
            cv2.setMouseCallback('selectBackground',lambda *args:None)
            cv2.createTrackbar('low threshold','selectBackground',0,255,nothing)
            cv2.createTrackbar('high threshold','selectBackground',0,255,nothing)
            cv2.createTrackbar('current ROI','selectBackground',0,ROINum,nothing)
            while lowThresh is None and highThresh is None:
                counter = 0
                bkgdOutput = np.zeros((h+50,w*2,3),'uint8')
                tempLowThresh = cv2.getTrackbarPos('low threshold','selectBackground')
                tempHighThresh = cv2.getTrackbarPos('high threshold','selectBackground')
#                 ROIInd = cv2.getTrackbarPos('current ROI','selectBackground')
                for stream in camList:
                    frame = stream.read()
                    frame = imutils.resize(frame,width=w,height=h)
                    
                    frameGray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                    frameGray = cv2.GaussianBlur(frameGray,(5,5),0)
                    
                    ROIUseList = ROIList[counter]
                    for ROIs in ROIUseList:
                        (ROIxuse,ROIyuse,ROIwuse,ROIhuse) = ROIs
                        frameDiff = cv2.absdiff(bkgd[0:h,0:w,counter],frameGray)
                        _, frameDiff = cv2.threshold(frameDiff,tempLowThresh,255,cv2.THRESH_TOZERO)
                        _, frameDiff = cv2.threshold(frameDiff,tempHighThresh,255,cv2.THRESH_TOZERO_INV)
                        _, frameDiff = cv2.threshold(frameDiff,3,255,cv2.THRESH_BINARY)
                        
                        if ROIxuse is not None:
                            mask = np.zeros_like(frameDiff,np.uint8)
                            cv2.rectangle(mask,(ROIxuse,ROIyuse),
                                          (ROIxuse+ROIwuse,ROIyuse+ROIhuse),
                                          (255,255,255),
                                          -1)
                            frameDiff = cv2.bitwise_and(frameDiff,mask)
                        
                        cnts = cv2.findContours(frameDiff.copy(),cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)[-2]
                        center = None
                        if len(cnts)>0:
                            c = max(cnts,key=cv2.contourArea)
                            ((x,y),radius) = cv2.minEnclosingCircle(c)
                                    
                            M = cv2.moments(c)
                            if radius > 10:
                                center = (int(M["m10"]/M["m00"]),int(M["m01"]/M["m00"]))                            
                                cv2.drawContours(frame, [c], -1, (0,255,255),2)
                                cv2.circle(frame,center,5,(0,0,255),-1)
                    bkgdOutput[0:h,w*counter:w*(counter+1)] = frame
                    counter+=1
                cv2.putText(bkgdOutput,'Select thresholds then press "space"',
                    (40,h + 30),
                        cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
                cv2.imshow('selectBackground',bkgdOutput)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord(" "):
                    lowThresh = tempLowThresh
                    highThresh = tempHighThresh
            cv2.destroyAllWindows()
            TTL1ts = list()
            TTL2ts = list()
            startTime = time.time()
    else:
        if writerList is None:
            cv2.namedWindow('comboImg')
            cv2.setMouseCallback('comboImg',buttonHandler2)
            now = datetime.now()
            saveName = now.strftime("%y%m%d-%H%M%S")
            saveName = "{}-{}".format(exptName,saveName)
            os.mkdir("/home/pi/CamSyncVids/{}".format(saveName))
            if trackingToggle:
                for i in range(len(bkgdList)):
                    cv2.imwrite("/home/pi/CamSyncVids/{}/{}_Cam{}Bkgd.png".format(saveName,saveName,i+1),bkgdList[i])
            writerList = list()
            for i in range(len(camList)):
                writer = cv2.VideoWriter("/home/pi/CamSyncVids/{}/{}_Cam{}.avi".format(saveName,saveName,i+1),fourcc,25,(w,h),True)
                writerList.append(writer)
            tsFile = open("/home/pi/CamSyncVids/{}/{}_timestamps.csv".format(saveName,saveName),'w')
            tsFileWriter = csv.writer(tsFile)
            headerRow = list()
            for i in range(len(camList)):
                headerRow.append("Cam{}".format(i+1))
                if trackingToggle:
                    for j in range(len(ROIList[i])):
                        headerRow.extend(["Cam{}{}CtrX".format(i+1,ROINameList[i][j]),
                                          "Cam{}{}CtrY".format(i+1,ROINameList[i][j]),
                                          "Cam{}{}Vel".format(i+1,ROINameList[i][j]),
                                          "Cam{}{}Rot".format(i+1,ROINameList[i][j])])
            headerRow.extend(["Keyboard1", "TTL1", "TTL2",
                                   "KnownDist", "Condit", "SyncFile"])
            tsFileWriter.writerow(headerRow)
        for stream in camList:
            frame = stream.read()
            ts = time.time()-startTime
            frame = imutils.resize(frame,width=w,height=h)
            camTsList[counter].append(ts)
            writerList[counter].write(frame)
            
            frameGray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            frameGray = cv2.GaussianBlur(frameGray,(5,5),0)
            
            if trackingToggle:
                ROIUseList = ROIList[counter]
                for idx, ROIs in enumerate(ROIUseList):
                    frameDiff = cv2.absdiff(bkgd[0:h,0:w,counter],frameGray)
                    _, frameDiff = cv2.threshold(frameDiff,lowThresh,255,cv2.THRESH_TOZERO)
                    _, frameDiff = cv2.threshold(frameDiff,highThresh,255,cv2.THRESH_TOZERO_INV)
                    _, frameDiff = cv2.threshold(frameDiff,3,255,cv2.THRESH_BINARY)
                    (ROIxuse,ROIyuse,ROIwuse,ROIhuse) = ROIs
                    if ROIxuse is not None:
                        mask = np.zeros_like(frameDiff,np.uint8)
                        cv2.rectangle(mask,(ROIxuse,ROIyuse),
                                      (ROIxuse+ROIwuse,ROIyuse+ROIhuse),
                                      (255,255,255),
                                      -1)
                        frameDiff = cv2.bitwise_and(frameDiff,mask)
                    
                    cnts = cv2.findContours(frameDiff.copy(),cv2.RETR_EXTERNAL,
                                            cv2.CHAIN_APPROX_SIMPLE)[-2]
                    center = None
                    rotState = None
                    if len(cnts)>0:
                        c = max(cnts,key=cv2.contourArea)
                        ((x,y),radius) = cv2.minEnclosingCircle(c)
        #                 if c.shape[0] > 5:
        #                     _,_,angle = cv2.fitEllipse(c)
        # #                     elli = cv2.fitEllipse(c)
        #                     if anglePrev is None:
        #                         anglePrev = angle
        #                     else:
        #                         rotState = rotCounter(angle,anglePrev)
        #                         anglePrev = angle
                                
                        M = cv2.moments(c)
                        if radius > 10 and trackingToggle:
                            center = (int(M["m10"]/M["m00"]),int(M["m01"]/M["m00"]))
                            miu20 = M["m20"]/M["m00"] - (M["m10"]/M["m00"])*(M["m10"]/M["m00"])
                            miu02 = M["m02"]/M["m00"] - (M["m01"]/M["m00"])*(M["m01"]/M["m00"])
                            miu11 = M["m11"]/M["m00"] - (M["m10"]/M["m00"])*(M["m01"]/M["m00"])
                            
                            b = 2*miu11
                            angle = .5*math.atan2(b,miu20-miu02)
                            deviation = math.sqrt(b*b+math.pow(miu20-miu02,2))
                            mjrAxisLength = math.sqrt(6* (miu20+miu02+deviation))
                            mnrAxisLength = math.sqrt(6* (miu20+miu02-deviation))
                            
                            if anglePrev[counter][idx] is None:
                                anglePrev[counter][idx] = angle
                            else:
                                rotState = rotCounter(angle,anglePrev[counter][idx])
                                anglePrev[counter][idx] = angle
                            
        #                     cv2.circle(frame, (int(x),int(y)), int(radius),
        #                                (0,255,255),2)
        #                     cv2.ellipse(frame, (center,(mjrAxisLength,mnrAxisLength),angle*180/np.pi),
        #                                 (255,0,255),2)
                            cv2.drawContours(frame, [c], -1, (0,255,255),2)
                            cv2.circle(frame,center,5,(0,0,255),-1)
                    if ROIShowCheck[counter]:
                        ROIalpha = .4
                        overlay = frame.copy()
                        cv2.rectangle(overlay,(ROIxuse,ROIyuse),
                                      (ROIxuse+ROIwuse,ROIyuse+ROIhuse),
                                      (255,0,0),
                                      -1)
                        cv2.putText(overlay,ROINameList[counter][idx],
                                    (ROIxuse,ROIyuse),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        cv2.addWeighted(overlay,ROIalpha,frame,1-ROIalpha,0,frame)
                    if ROIStatList[counter][idx]:
                        overlay = frame.copy()
                        cv2.rectangle(overlay,(0,0),
                                      (w//2,h//2),
                                      (150,150,150),
                                      -1)
                        cv2.putText(frame,
                                    ROINameList[counter][idx],
                                    (10,20),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        cv2.putText(frame,
                                    'Coordinates:{}'.format(center),
                                    (10,50),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        cv2.putText(frame,
                                    'Ipsi Rotations:{}'.format(camRotList[counter][idx].count(-1)),
                                    (10,80),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        cv2.putText(frame,
                                    'Contra Rotations:{}'.format(camRotList[counter][idx].count(1)),
                                    (10,110),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        cv2.addWeighted(overlay,buttonAlpha,frame,1-buttonAlpha,0,frame)
                    if center is not None:
                        tempctrx,tempctry = center
                        camCtrXList[counter][idx].append(tempctrx)
                        camCtrYList[counter][idx].append(tempctry)
                    else:
                        camCtrXList[counter][idx].append(None)
                        camCtrYList[counter][idx].append(None)
                    camRotList[counter][idx].append(rotState)
            
            output[0:h,w*counter:w*(counter+1)] = frame
#             diffHolder[0:h,w*counter:w*(counter+1)] = frameDiff
            
            timeStamps[counter] = ts
            counter +=1
        cv2.putText(output,'{}'.format(timeStamps[0]),(10,h-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,0,255),1)
        cv2.putText(output,'{}'.format(timeStamps[1]),(w+10,h-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,0,255),1)
        
        minTime = np.floor(ts/timeLength)*timeLength
        maxTime = np.ceil(ts/timeLength)*timeLength
        realDiv = ts/timeLength
        frac = realDiv-minTime/timeLength
        cv2.putText(output,'{}'.format(minTime),(10,output.shape[0]-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(output,'{}'.format(maxTime),(2*w-50,output.shape[0]-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(output,'M1',(10,h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(output,'I1',(10,h + 40),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(output,'I2',(10,h + 60),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        if showPulseCounts:
            cv2.putText(output,'{}'.format(len(keyboard1ts)),(30,h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(150,150,150),1)
            cv2.putText(output,'{}'.format(len(TTL1ts)),(30,h + 40),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(150,150,150),1)
            cv2.putText(output,'{}'.format(len(TTL2ts)),(30,h + 60),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(150,150,150),1)
        cv2.line(output,(int((2*w-2*lineBarrier)*frac+lineBarrier),h  + 10),
                (int((2*w-2*lineBarrier)*frac+lineBarrier),h + extraSpace -10),
                (255,255,255),3)
        if graphCheck == minTime:
            if len(lineHolder)>1000:
                plotter = lineHolder[-1000:-1]
            else:
                plotter = lineHolder
            for lines in plotter:
                cv2.line(output,(int((2*w-2*lineBarrier)*lines+lineBarrier),h+10),
                (int((2*w-2*lineBarrier)*lines+lineBarrier),h+25),
                (0,0,255),1)
        elif graphCheck != minTime and graphCheck != -1:
            graphCheck = -1
            lineHolder = list()
            
        if graphCheck2 == minTime:
            if len(lineHolder2)>1000:
                plotter = lineHolder2[-1000:-1]
            else:
                plotter = lineHolder2
            for lines in plotter:
                cv2.line(output,(int((2*w-2*lineBarrier)*lines+lineBarrier),h+30),
                (int((2*w-2*lineBarrier)*lines+lineBarrier),h+45),
                (0,255,0),1)
        elif graphCheck2 != minTime and graphCheck2 != -1:
            graphCheck2 = -1
            lineHolder2 = list()
            
        if graphCheck3 == minTime:
            if len(lineHolder3)>1000:
                plotter = lineHolder3[-1000:-1]
            else:
                plotter = lineHolder3
            for lines in plotter:
                cv2.line(output,(int((2*w-2*lineBarrier)*lines+lineBarrier),h+50),
                (int((2*w-2*lineBarrier)*lines+lineBarrier),h+65),
                (255,255,0),1)
        elif graphCheck3 != minTime and graphCheck3 != -1:
            graphCheck3 = -1
            lineHolder3 = list()
        
#         if swapVids:
#             outputTemp = output.copy()
#             output[0:h,0:w] = outputTemp[0:h,w:2*w]
#             output[0:h,w:w*2] = outputTemp[0:h,0:w]
        
        overlay = output.copy()
#         cv2.rectangle(overlay,(2*w-25,h-25),
#                               (2*w,h-1),
#                               (150,150,150),
#                               -1)
#         cv2.rectangle(overlay,(2*w-25,h-25),
#                               (2*w,h-1),
#                               (255,255,255),
#                               1)
#         cv2.putText(overlay,'< >',(2*w-20,h-10),
#                         cv2.FONT_HERSHEY_SIMPLEX,0.25,(255,255,255),2)
        cv2.rectangle(overlay,(2*w-25,h+10),
                              (2*w,h+35),
                              (150,150,150),
                              -1)
        cv2.rectangle(overlay,(2*w-25,h+10),
                              (2*w,h+35),
                              (255,255,255),
                              1)
        cv2.arrowedLine(overlay,(2*w-12,h+28),
                        (2*w-12,h+17),
                        (255,255,255),2,cv2.LINE_AA,tipLength=.5)
        cv2.rectangle(overlay,(2*w-25,h+50),
                              (2*w,h+75),
                              (150,150,150),
                              -1)
        cv2.rectangle(overlay,(2*w-25,h+50),
                              (2*w,h+75),
                              (255,255,255),
                              1)
        cv2.arrowedLine(overlay,(2*w-12,h+57),
                        (2*w-12,h+68),
                        (255,255,255),2,cv2.LINE_AA,tipLength=.5)
        cv2.addWeighted(overlay,buttonAlpha,output,1-buttonAlpha,0,output)
        
        cv2.imshow('comboImg',output)
    #     cv2.imshow('subtracted',diffHolder)
        if ts>shutoffTime:
            break
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

for i in range(len(camVelList)):
    for j in range(len(camVelList[i])):
        camVelList[i][j].append(None)
        for ind in range(len(camCtrXList[i][j])-1):
            if camCtrXList[i][j][ind] is not None and camCtrXList[i][j][ind+1] is not None:
                timeDiff1 = camTsList[i][ind+1]-camTsList[i][ind]
                camVelList[i][j].append((math.hypot(camCtrXList[i][j][ind+1]-camCtrXList[i][j][ind],
                                          camCtrYList[i][j][ind+1]-camCtrYList[i][j][ind])
                                /timeDiff1)/(knownDist[0]/25)) #This 25cm is specific to our circular open field!
            else:
                camVelList[i][j].append(None)

toZipRow = list()
for i in range(len(camList)):
    toZipRow.append(camTsList[i])
    if trackingToggle:
        for j in range(len(ROIList[i])):
            toZipRow.extend([camCtrXList[i][j],
                             camCtrYList[i][j],
                             camVelList[i][j],
                             camRotList[i][j]])
toZipRow.extend([keyboard1ts, TTL1ts, TTL2ts,
                 knownDist, [condit], [syncFile]])

for row in zip_longest(*toZipRow):
    tsFileWriter.writerow(row)
tsFile.flush()
tsFile.close()      
cv2.destroyAllWindows()
for stream in camList:
    stream.stop()
for writer in writerList:
    writer.release()


