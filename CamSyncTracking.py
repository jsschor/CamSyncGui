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
import wavePWM
from subprocess import call

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
distConv = 1
CamTrigIO = 14

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
ROIInd = None
trackROITouch = None

camTsList = list()
camCtrXList = list()
camCtrYList = list()
camVelList = list()
camRotList = list()
IONameList = list()
IOTypeList = list()
keyboardTrigList = list()
IOTsList = list()
lineHolderList = list()
graphCheckList = list()
keyboard1ts = list()
TTL1ts = list()
TTL2ts = list()
camList = list()
graphShowInds = np.array([0,1,2])
timeLength = 30

IONameList = ['Drg1','Drg2','Dorc','Stim','Cam1']
IOTypeList = [0,0,1,1,2]
GPIOList = [24,25,CamTrigIO]
StepList = list()
SubStepList = list()

#Make new class for initial dialog box
class StartDialog(tkSimpleDialog.Dialog):
    global IONameList
    global IOTypeList
    global GPIOList
    global StepList
    global SubStepList
    
    def __init__(self,parent,title=None):
        global IONameList
        global IOTypeList
        global GPIOList
        global StepList
        global SubStepList
        
        Toplevel.__init__(self,parent)
        self.transient(parent)
        
        if title:
            self.title(title)
        
        self.parent = parent
        self.result = None
        
        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5,pady=5)
        
        self.buttonbox()
        
        self.grab_set()
        
        self.IONameList = IONameList
        self.IOTypeList = IOTypeList
        self.GPIOList = GPIOList
        self.StepList = StepList
        self.SubStepList = SubStepList
        
        if not self.initial_focus:
            self.initial_focus = self
            
        self.protocol("WM_DELETE_WINDOW",self.cancel)
        self.geometry("+%d+%d"%(parent.winfo_rootx()+50,
                                parent.winfo_rooty()+50))
        
        self.initial_focus.focus_set()
        
        self.wait_window(self)
    def body(self,master):
        Label(master,text="Enter an experiment name:").grid(row=0,sticky=W)
        Label(master,text="Enter experiment condition:").grid(row=1,sticky=W)
        Label(master,text="Enter sync'd file name:").grid(row=2,sticky=W)
        Label(master,text="Enter recording time in secs (leave blank for inf):").grid(row=3,sticky=W)
        Label(master,text="Fill out below if tracking").grid(row=7,sticky=W)
        Label(master,text="Enter known distance").grid(row=8,sticky=W)
        Label(master,text="Enter number of ROIs").grid(row=9,sticky=W)
        
        self.e1 = Entry(master)
        self.e2 = Entry(master)
        self.e3 = Entry(master)
        self.e4 = Entry(master)
        self.e5 = Entry(master)
        self.e6 = Entry(master)
        
        self.e5.insert(END,'25')
        self.e6.insert(END,'2')
        
        self.e1.grid(row=0,column=1)
        self.e2.grid(row=1,column=1)
        self.e3.grid(row=2,column=1)
        self.e4.grid(row=3,column=1)
        self.e5.grid(row=8,column=1)
        self.e6.grid(row=9,column=1)
        
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
        distConv = float(self.e5.get())
        ROINum = int(self.e6.get())
        IONameList = self.IONameList
        IOTypeList = self.IOTypeList
        GPIOList = self.GPIOList
        StepList = self.StepList
        SubStepList = self.SubStepList
        self.result = (exptName,condit,syncFile,shutoffTime,
                       trackingToggle,twoCam,distConv,ROINum,
                       IONameList,IOTypeList,GPIOList,
                       StepList,SubStepList)

#Allow for user to put in experiment name
askWindow = tk.Tk()
d = StartDialog(askWindow)
[exptName,condit,syncFile,shutoffTime,
 trackingToggle,twoCam,distConv,ROINum,
 IONameList,IOTypeList,GPIOList,
 StepList,SubStepList] = d.result
# print(StepList)
# print(SubStepList)
if len(shutoffTime)==0:
    shutoffTime = np.inf
else:
    shutoffTime = float(shutoffTime)
askWindow.destroy()

colorList = list()
for i in range(len(IONameList)):
    colorList.append(tuple([int(x) for x in np.random.choice(range(100,256),size=3)]))
keyboardTrigList = range(1,IOTypeList.count(0)+1)

for names in IONameList:
    IOTsList.append(list())
    lineHolderList.append(list())
    graphCheckList.append(-1)

GPIO = pigpio.pi()
pwm = wavePWM.PWM(GPIO)

def cbf(g,l,t):
    global graphCheck2,lineHolder2,minTime,startTime,timeLength
    global GPIOList,keyboardTrigList,IOTsList
    
    ind = GPIOList.index(g)
    trueInd = ind+len(keyboardTrigList)
    ts = time.time()-startTime
    realDiv = ts/timeLength
    frac = realDiv-minTime/timeLength
    IOTsList[trueInd].append(ts)
    lineHolderList[trueInd].append(frac)
    if graphCheckList[trueInd] == -1:
        graphCheckList[trueInd] = minTime
outputInd = 0
for ind, GPz in enumerate(GPIOList):
    trueInd = ind+len(keyboardTrigList)
    if IOTypeList[trueInd] == 1:
        GPIO.set_mode(GPz,pigpio.INPUT)
        GPIO.set_pull_up_down(GPz,pigpio.PUD_UP)
    elif IOTypeList[trueInd] == 2 and GPz == CamTrigIO:
        GPIO.set_mode(GPz,pigpio.OUTPUT)
    elif IOTypeList[trueInd] == 3:
        GPIO.set_mode(GPz,pigpio.OUTPUT)
        GPIO.write(GPz,1)
    elif IOTypeList[trueInd] == 4:
        GPIO.set_mode(GPz,pigpio.OUTPUT)
        GPIO.write(GPz,0)
    elif IOTypeList[trueInd] == 2 and GPz != CamTrigIO:
        for inder, steppee in enumerate(StepList[outputInd]):
            if ',' in steppee:
                freq = int((steppee.split('). '))[1].split('Hz')[0])
                PW = int((steppee.split('Hz, '))[1].split('us')[0])
                repeats = int((steppee.split('us, '))[1].split(' times')[0])
                print(freq)
                print(PW)
                print(repeats)
                if freq == 0:
                    pwm.updateWaveChainDelaySeconds(GPz,repeats)
                else:
                    pwm.updateWaveChainSeconds(GPz,freq,0,PW,repeats)
            else:
                superRepeats = int((steppee.split('). '))[1].split(' times')[0])
                print(superRepeats)
                pwm.updateWaveChainStartLoop()
                for subbee in SubStepList[outputInd][inder]:
                    freq = int((subbee.split('). '))[1].split('Hz')[0])
                    PW = int((subbee.split('Hz, '))[1].split('us')[0])
                    repeats = int((subbee.split('us, '))[1].split(' times')[0])
                    print(freq)
                    print(PW)
                    print(repeats)
                    if freq == 0:
                        pwm.updateWaveChainDelaySeconds(GPz,repeats)
                    else:
                        pwm.updateWaveChainSeconds(GPz,freq,0,PW,repeats)
                pwm.updateWaveChainEndLoop(superRepeats)
        outputInd+=1
#         pwm.updateWaveChainSeconds(GPz,1,0,1000,1)
#         pwm.updateWaveChainStartLoop()
#         pwm.updateWaveChainDelaySeconds(GPz,10)
#         pwm.updateWaveChainSeconds(GPz,20,0,60,10)
#         pwm.updateWaveChainEndLoop(5)
#         pwm.updateWaveChainDelaySeconds(GPz,10)
#         pwm.updateWaveChainSeconds(GPz,1,0,1000,1)
    
    GPIO.callback(GPz, pigpio.RISING_EDGE,cbf)
while len(IONameList)<3:
    IONameList.append('')
    IOTsList.append(list())
# GPIO = pigpio.pi()
# inputPin1 = 24
# GPIO.set_mode(inputPin1,pigpio.INPUT)
# GPIO.set_pull_up_down(inputPin1,pigpio.PUD_UP)
# inputPin2 = 25
# GPIO.set_mode(inputPin2,pigpio.INPUT)
# GPIO.set_pull_up_down(inputPin2,pigpio.PUD_UP)

h = 240
w = 320
call(["sudo","modprobe","bcm2835-v4l2"])
if twoCam:
    cap = VideoStream(src=0,resolution=(w,h)).start()
    # cap2 = VideoStream(usePiCamera=True).start()
    cap2 = VideoStream(src=3,resolution=(w,h)).start()
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
    threshHolder = [list(),list()]
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
    threshHolder = [list()]
time.sleep(2.0)


bkgd = np.zeros((h,w,2),'uint8')
diffHolder = np.zeros((h,w*2),'uint8')
lowThresh = None
highThresh = None
knownDist = None
firstPoint = None
(ROIx1,ROIy1,ROIw1,ROIh1) = (None,None,None,None)
(ROIx2,ROIy2,ROIw2,ROIh2) = (None,None,None,None)
ix = 0
iy = 0
ix2 = 0
iy2 = 0
replotInd = -1

angleAcc = 0
angle = None
global stimCount
global stimCount2
stimCount = 1
stimCount2 = 1

# def cbf(g,l,t):
#     global graphCheck2
#     global lineHolder2
#     global inputPin1
#     global minTime
#     global startTime
#     global timeLength
#     global stimCount
#     global TTL1ts
#     
# #     print(stimCount)
#     stimCount+=1
#     
#     ts = time.time()-startTime
#     realDiv = ts/timeLength
#     frac = realDiv-minTime/timeLength
#     TTL1ts.append(ts)
#     lineHolder2.append(frac)
#     if graphCheck2 == -1:
#         graphCheck2 = minTime
#             
# # GPIO.callback(inputPin1, pigpio.RISING_EDGE,cbf)
# 
# def cbf2(g,l,t):
#     global graphCheck3
#     global lineHolder3
#     global inputPin2
#     global minTime
#     global startTime
#     global timeLength
#     global stimCount2
#     global TTL2ts
#     
# #     print(stimCount2)
#     stimCount2+=1
#     
#     ts = time.time()-startTime
#     realDiv = ts/timeLength
#     frac = realDiv-minTime/timeLength
#     TTL2ts.append(ts)
#     lineHolder3.append(frac)
#     if graphCheck3 == -1:
#         graphCheck3 = minTime
# 
# GPIO.callback(inputPin2, pigpio.RISING_EDGE,cbf2)

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
    global lineBarrier,graphShowInds,replotInd
    if event==cv2.EVENT_LBUTTONDOWN and x>output.shape[1]-25:
        if y>h-25 and y<h:
            swapVids = not swapVids
        elif y>h+10 and y<h+35:
            if graphShowInds[0]>0:
                graphShowInds -= 1
                i = np.where(graphShowInds==graphShowInds[0])
                i = i[0]
                output[h+10+int(i)*20:h+26+int(i)*20,lineBarrier:2*w-lineBarrier,:] = np.zeros((16,2*(w-lineBarrier),3),'uint8')
                replotInd = graphShowInds[0]
        elif y>h+50 and y<h+75:
            if graphShowInds[-1]<len(IONameList)-1:
                graphShowInds += 1
                i = np.where(graphShowInds==graphShowInds[-1])
                i = i[0]
                output[h+10+int(i)*20:h+26+int(i)*20,lineBarrier:2*w-lineBarrier,:] = np.zeros((16,2*(w-lineBarrier),3),'uint8')
                replotInd = graphShowInds[-1]
                
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

#Set slider val
def getROISlider(value):
    global threshHolder,ROIInd,ROIList,trackROITouch
    trackROITouch = 1
    ROIInd = value
    counter = 0
    if ROIInd>len(ROIList[0])-1:
        counter=1
    if threshHolder[counter][ROIInd-counter*len(ROIList[0])] is not None:
        cv2.setTrackbarPos('low threshold','selectBackground',
                           threshHolder[counter][ROIInd-counter*len(ROIList[0])][0])
        cv2.setTrackbarPos('high threshold','selectBackground',
                           threshHolder[counter][ROIInd-counter*len(ROIList[0])][1])

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
    lineBarrier = 100
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
                        threshHolder[0].append(None)
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
                        threshHolder[1].append(None)
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
            bkgdOutputSave = np.copy(bkgdOutput)
            cv2.setMouseCallback('selectBackground',draw)
            doneDist = None
            if len(ROINameList)<2:
                knownDist = [-1]
                camDistInd = 0
            elif len(ROINameList[0])>0 and len(ROINameList[1])>0:  
                knownDist = [-1,-1]
                camDistInd = 0
            elif len(ROINameList[0])>0 and len(ROINameList[1])==0:
                knownDist = [-1]
                camDistInd = 0
            elif len(ROINameList[0])==0 and len(ROINameList[1])>0:
                knownDist = [-1]
                camDistInd = 1
            distInd = 0
            while doneDist == None:
                bkgdOutput = np.copy(bkgdOutputSave)
                if distInd == 0:
                    cv2.putText(bkgdOutput,'Draw known distance for left cam',
                        (40,h + int(6*extraSpace/10)),
                            cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
                    cv2.putText(bkgdOutput,'then press "space"',
                        (40,h + int(8*extraSpace/10)),
                            cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
                elif distInd == 1:
                    cv2.putText(bkgdOutput,'Draw known distance for right cam',
                        (40,h + int(6*extraSpace/10)),
                            cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
                    cv2.putText(bkgdOutput,'then press "space"',
                        (40,h + int(8*extraSpace/10)),
                            cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1)
                cv2.line(bkgdOutput,pt1=(ix,iy),pt2=(ix2,iy2),
                 color=(255,255,255),
                 thickness=2)
                if (ix,iy,ix2,iy2)!=(0,0,0,0):
                    cv2.putText(bkgdOutput,'{}'.format(distConv),
                            (ix2+10,iy2+10),
                                cv2.FONT_HERSHEY_SIMPLEX,.35,(255,255,255),1)
                cv2.imshow('selectBackground',bkgdOutput)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord(" "):
                    a = np.array((ix,iy))
                    b = np.array((ix2,iy2))
                    knownDist[distInd] = [np.linalg.norm(a-b)]
                    if -1 not in knownDist:
                        doneDist = 1
                    else:
                        distInd = 1
            cv2.setMouseCallback('selectBackground',lambda *args:None)
            cv2.createTrackbar('low threshold','selectBackground',0,255,nothing)
            cv2.createTrackbar('high threshold','selectBackground',0,255,nothing)
            if ROINum>1:
                cv2.createTrackbar('current ROI','selectBackground',0,ROINum-1,getROISlider)
            while lowThresh is None and highThresh is None:
                counter = 0
                bkgdOutput = np.zeros((h+50,w*2,3),'uint8')
                if ROIInd is None:
                    ROIInd = 0
                tempLowThresh = cv2.getTrackbarPos('low threshold','selectBackground')
                tempHighThresh = cv2.getTrackbarPos('high threshold','selectBackground')
                
                tempCount = 0
                if ROIInd>len(ROIList[0])-1:
                    tempCount=1
                threshHolder[tempCount][ROIInd-tempCount*len(ROIList[0])] = [tempLowThresh,tempHighThresh]
                for stream in camList:
                    frame = stream.read()
                    frame = imutils.resize(frame,width=w,height=h)
                    
                    frameGray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                    frameGray = cv2.GaussianBlur(frameGray,(5,5),0)
                    
                    ROIUseList = ROIList[counter]
                    for idx,ROIs in enumerate(ROIUseList):
                        if trackROITouch is None:
                            threshHolder[counter][idx] = [tempLowThresh,tempHighThresh]
                        (ROIxuse,ROIyuse,ROIwuse,ROIhuse) = ROIs
                        frameDiff = cv2.absdiff(bkgd[0:h,0:w,counter],frameGray)
                        _, frameDiff = cv2.threshold(frameDiff,threshHolder[counter][idx][0],255,cv2.THRESH_TOZERO)
                        _, frameDiff = cv2.threshold(frameDiff,threshHolder[counter][idx][1],255,cv2.THRESH_TOZERO_INV)
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
                        if idx+counter*len(ROIList[0])==ROIInd:
                            ROIalpha = .4
                            overlay = frame.copy()
                            cv2.rectangle(overlay,(ROIxuse,ROIyuse),
                                      (ROIxuse+ROIwuse,ROIyuse+ROIhuse),
                                      (255,0,0),
                                      -1)
                            cv2.putText(overlay,ROINameList[counter][idx],
                                    (ROIxuse+10,ROIyuse+10),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                            cv2.addWeighted(overlay,ROIalpha,frame,1-ROIalpha,0,frame)
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
                    lowThresh = 1
                    highThresh = 1
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
                headerRow.append("Cam{}ts".format(i+1))
                if trackingToggle:
                    for j in range(len(ROIList[i])):
                        headerRow.extend(["Cam{}{}CtrX".format(i+1,ROINameList[i][j]),
                                          "Cam{}{}CtrY".format(i+1,ROINameList[i][j]),
                                          "Cam{}{}Vel".format(i+1,ROINameList[i][j]),
                                          "Cam{}{}Rot".format(i+1,ROINameList[i][j])])
            headerRow.extend(IONameList)
            if knownDist is not None:
                for i in range(len(knownDist)):
                    if len(knownDist)<2:
                        headerRow.append("KnownDistCam{}".format(camDistInd+1))
                    else:
                        headerRow.append("KnownDistCam{}".format(i+1))
            headerRow.extend(["Condit", "SyncFile"])
            tsFileWriter.writerow(headerRow)
            if IOTypeList.count(2)>1:
                pwm.startWaveChain()
            lineGraphHolder = [np.zeros((16,2*(w-lineBarrier),3),'uint8')]*(len(IONameList)+1)
            startTime = time.time()
        for stream in camList:
            frame = stream.read()
            ts = time.time()-startTime
            frame = imutils.resize(frame,width=w,height=h)
            camTsList[counter].append(ts)
            writerList[counter].write(frame)
            
            if counter == 0:
                GPIO.gpio_trigger(CamTrigIO,60,1)
            
            frameGray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            frameGray = cv2.GaussianBlur(frameGray,(5,5),0)
            
            if trackingToggle:
                ROIUseList = ROIList[counter]
                for idx, ROIs in enumerate(ROIUseList):
                    frameDiff = cv2.absdiff(bkgd[0:h,0:w,counter],frameGray)
                    _, frameDiff = cv2.threshold(frameDiff,threshHolder[counter][idx][0],255,cv2.THRESH_TOZERO)
                    _, frameDiff = cv2.threshold(frameDiff,threshHolder[counter][idx][1],255,cv2.THRESH_TOZERO_INV)
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
                    
                    if center is not None:
                        tempctrx,tempctry = center
                        camCtrXList[counter][idx].append(tempctrx)
                        camCtrYList[counter][idx].append(tempctry)
                        if len(camCtrXList[counter][idx])>1 and camCtrXList[counter][idx][-2] is not None:
                            timeDiff1 = camTsList[counter][-1]-camTsList[counter][-2]
                            camVelList[counter][idx].append((math.hypot(camCtrXList[counter][idx][-1]-camCtrXList[counter][idx][-2],
                                                                camCtrYList[counter][idx][-1]-camCtrYList[counter][idx][-2])
                                                     /timeDiff1)/(knownDist[counter*(len(knownDist)-1)][0]/distConv))
                        else:
                            camVelList[counter][idx].append(None)
                    else:
                        camCtrXList[counter][idx].append(None)
                        camCtrYList[counter][idx].append(None)
                        camVelList[counter][idx].append(None)
                    camRotList[counter][idx].append(rotState)
                    
                    if ROIShowCheck[counter]:
                        ROIalpha = .4
                        overlay = frame.copy()
                        cv2.rectangle(overlay,(ROIxuse,ROIyuse),
                                      (ROIxuse+ROIwuse,ROIyuse+ROIhuse),
                                      (255,0,0),
                                      -1)
                        cv2.putText(overlay,ROINameList[counter][idx],
                                    (ROIxuse+10,ROIyuse+10),
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
                                    (10,40),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        if camVelList[counter][idx][-1] is not None:
                            cv2.putText(frame,
                                        'Velocity:{:0.2f}'.format(camVelList[counter][idx][-1]),
                                        (10,60),
                                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        else:
                            cv2.putText(frame,
                                        'Velocity:'.format(camVelList[counter][idx][-1]),
                                        (10,60),
                                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        cv2.putText(frame,
                                    'Ipsi Rotations:{}'.format(camRotList[counter][idx].count(-1)),
                                    (10,80),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        cv2.putText(frame,
                                    'Contra Rotations:{}'.format(camRotList[counter][idx].count(1)),
                                    (10,100),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
                        cv2.addWeighted(overlay,buttonAlpha,frame,1-buttonAlpha,0,frame)
            
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
        cv2.putText(output,'{}'.format(minTime),(lineBarrier-30,output.shape[0]-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(output,'{}'.format(maxTime),(2*w-50,output.shape[0]-10),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(output,'{}'.format(IONameList[graphShowInds[0]]),(10,h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(output,'{}'.format(IONameList[graphShowInds[1]]),(10,h + 40),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        cv2.putText(output,'{}'.format(IONameList[graphShowInds[2]]),(10,h + 60),
                        cv2.FONT_HERSHEY_SIMPLEX,0.35,(255,255,255),1)
        for inds in range(len(graphCheckList)):
            if graphCheckList[inds] == minTime:
                if len(lineHolderList[inds])>100:
                    plotter = lineHolderList[inds][-100:-1]
                else:
                    plotter = lineHolderList[inds]
                if inds in graphShowInds:
                    i = np.where(graphShowInds==inds)
                    i = i[0]
                    output[h+10+int(i)*20:h+26+int(i)*20,lineBarrier:2*w-lineBarrier,:] = lineGraphHolder[inds].copy()
                    if replotInd == inds:
                        plotter = plotter
                        replotInd = -1
                    else:
                        plotter = [plotter[-1]]
                    for lines in plotter:
                        cv2.line(output,(int((2*w-2*lineBarrier)*lines+lineBarrier),h+10+i*20),
                        (int((2*w-2*lineBarrier)*lines+lineBarrier),h+25+i*20),
                        colorList[inds],1)
                    lineGraphHolder[inds] = output[h+10+int(i)*20:h+26+int(i)*20,lineBarrier:2*w-lineBarrier,:].copy()
            elif graphCheckList[inds] != minTime and graphCheckList[inds] != -1:
                graphCheckList[inds] = -1
                lineHolderList[inds] = list()
                lineGraphHolder[inds] = np.zeros((16,2*(w-lineBarrier),3),'uint8')
            else:
                lineGraphHolder[inds] = np.zeros((16,2*(w-lineBarrier),3),'uint8')
        cv2.line(output,(int((2*w-2*lineBarrier)*frac+lineBarrier),h  + 10),
                (int((2*w-2*lineBarrier)*frac+lineBarrier),h + extraSpace -10),
                (255,255,255),3)
        if showPulseCounts:
            for i in range(3):
                if IONameList[graphShowInds[i]] == 'Cam1':
                    cv2.putText(output,'{:0.1f}fps'.format(len(IOTsList[graphShowInds[i]])/ts),(50,h + 20*(i+1)),
                                cv2.FONT_HERSHEY_SIMPLEX,0.35,(150,150,150),1)
                else:
                    cv2.putText(output,'{}'.format(len(IOTsList[graphShowInds[i]])),(50,h + 20*(i+1)),
                                cv2.FONT_HERSHEY_SIMPLEX,0.35,(150,150,150),1)
            
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
        if ts>shutoffTime:
            break
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        for trig in keyboardTrigList:
            if key == ord("{}".format(trig)):
                IOTsList[trig-1].append(ts)
                lineHolderList[trig-1].append(frac)
                if graphCheckList[trig-1] == -1:
                    graphCheckList[trig-1] = minTime
    
# for i in range(len(camVelList)):
#     for j in range(len(camVelList[i])):
#         camVelList[i][j].append(None)
#         for ind in range(len(camCtrXList[i][j])-1):
#             if camCtrXList[i][j][ind] is not None and camCtrXList[i][j][ind+1] is not None:
#                 timeDiff1 = camTsList[i][ind+1]-camTsList[i][ind]
#                 camVelList[i][j].append((math.hypot(camCtrXList[i][j][ind+1]-camCtrXList[i][j][ind],
#                                           camCtrYList[i][j][ind+1]-camCtrYList[i][j][ind])
#                                 /timeDiff1)/(knownDist[0]/25)) #This 25cm is specific to our circular open field!
#             else:
#                 camVelList[i][j].append(None)

toZipRow = list()
for i in range(len(camList)):
    toZipRow.append(camTsList[i])
    if trackingToggle:
        for j in range(len(ROIList[i])):
            toZipRow.extend([camCtrXList[i][j],
                             camCtrYList[i][j],
                             camVelList[i][j],
                             camRotList[i][j]])
toZipRow.extend(IOTsList)
if knownDist is not None:
    for i in range(len(knownDist)):
        toZipRow.append(knownDist[i])
toZipRow.extend([[condit], [syncFile]])
for row in zip_longest(*toZipRow):
    tsFileWriter.writerow(row)
tsFile.flush()
tsFile.close()      
cv2.destroyAllWindows()
pwm.cancel()
GPIO.stop()
for stream in camList:
    stream.stop()
for writer in writerList:
    writer.release()

