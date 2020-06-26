from tkinter import *
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import ttk
import os
import cv2
import numpy as np
import ast
import pickle

class Dialog(Toplevel):
    def __init__(self,parent,title=None):
        pass
        
    def body(self,master):
        pass
        
    def buttonbox(self):
            
        box = Frame(self)
            
        w = Button(box,text="OK",width=10,command=self.ok,default=ACTIVE)
        w.pack(side=BOTTOM,padx=5,pady=5)
        w = Button(box,text="Change I/O", width=10,command=self.ioOpen)
        w.pack(side=BOTTOM,padx=5,pady=5)
        w = Button(box,text="Save Config", width=10,command=self.saveConfig)
        w.pack(side=BOTTOM,padx=5,pady=5)
        w = Button(box,text="Load Config", width=10,command=self.loadConfig)
        w.pack(side=BOTTOM,padx=5,pady=5)
        
        self.bind("<Return>",self.ok)
        
        box.pack()
            
    def ok(self,event=None):
            
        if not self.validate():
            self.initial_focus.focus_set()
            return
            
        self.withdraw()
        self.update_idletasks()
            
        self.apply()
        self.cancel()
            
    def cancel(self,event=None):
        self.parent.focus_set()
        self.destroy()
        
    def saveConfig(self,event=None):
        self.grab_release()
        nameSaveWindow = tk.Tk()
        saveName = simpledialog.askstring("Save Config",
                                         "Save Name:",
                                         parent=nameSaveWindow,
                                         initialvalue="")
        nameSaveWindow.destroy()
        f= open('/home/pi/CamSyncConfigs/{}.pickle'.format(saveName),'wb')
        pickle.dump([self.IONameList,
                     self.IOTypeList,
                     self.GPIOList,
                     self.StepList,
                     self.SubStepList,
                     self.e1.get(),
                     self.e2.get(),
                     self.e3.get(),
                     self.e4.get(),
                     self.cbState.get(),
                     self.cbState2.get(),
                     float(self.e5.get()),
                     int(self.e6.get())],f)
        f.close()
        self.grab_set()
    def loadConfig(self,event=None):
        self.grab_release()
        root = tk.Tk()
        loadName = askopenfilename(parent=root)
        root.destroy()
        f = open(loadName,'rb')
        self.IONameList,self.IOTypeList,self.GPIOList,self.StepList,self.SubStepList,exptName,condit,syncFile,shutoffTime,trackingToggle,twoCam,distConv,ROINum = pickle.load(f)
        f.close()
        
        self.e1.delete(0,END)
        self.e2.delete(0,END)
        self.e3.delete(0,END)
        self.e4.delete(0,END)
        self.e5.delete(0,END)
        self.e6.delete(0,END)
        
        self.e1.insert(END,exptName)
        self.e2.insert(END,condit)
        self.e3.insert(END,syncFile)
        self.e4.insert(END,shutoffTime)
        self.e5.insert(END,distConv)
        self.e6.insert(END,ROINum)
        
        self.cbState.set(trackingToggle)
        self.cbState2.set(twoCam)
        
        
        self.grab_set()
        print(self.IONameList)
    def ioOpen(self,event=None):
        global w,h,bS,leftRow,leftRowFill,leftRowBorder
        global rightRow,rightRowFill,rightRowBorder
        global keyRow,keyRowFill,saveCheck
        global leftRowSteps,leftRowSubSteps
        global rightRowSteps,rightRowSubSteps
        
        sided = -1
        ind = None
        name = None
        
        self.grab_release()
        
        class GPIODialog(tk.simpledialog.Dialog):
            def buttonbox(self):
                box = Frame(self) 
                w = Button(box,text="OK",width=10,command=self.ok,default=ACTIVE)
                w.pack(side=BOTTOM,padx=5,pady=5)                
                self.bind("<Return>",self.ok)
                box.pack()
            def body(self,master):
                global ind,name,leftRowFill,leftRowBorder
                global rightRow,rightRowFill,rightRowBorder,sided
                global leftRowSteps,leftRowSubSteps
                global rightRowSteps,rightRowSubSteps
                Label(master,text="Enter a name for this port:").grid(row=0,sticky=W)
                Label(master,text="Enter a 4-character shorthand:").grid(row=1,sticky=W)
                if sided == 0:
                    longName = name
                    shortName = name
                    currFill = leftRowFill[ind]
                    currBord = leftRowBorder[ind]
                    currSteps = leftRowSteps[ind]
                    currSubSteps = leftRowSubSteps[ind]
                elif sided==1:
                    longName = name
                    shortName = name
                    currFill = rightRowFill[ind]
                    currBord = rightRowBorder[ind]
                    currSteps = rightRowSteps[ind]
                    currSubSteps = rightRowSubSteps[ind]
                self.e1 = Entry(master)
                self.e2 = Entry(master)
                                
                self.e1.insert(END,longName)
                self.e2.insert(END,shortName)
                
                self.e1.grid(row=0,column=1)
                self.e2.grid(row=1,column=1)
                
                self.rbState = StringVar(master=master)
                self.rbState.set(str(currFill))
                
                MODES = [('Input','(0, 255, 0)'),('Output','(255, 0, 0)'),('High','(255, 255, 0)'),('Low','(0, 255, 255)'),('Off','(0, 0, 0)')]
                
                for ind, val in enumerate(MODES):
                    self.rb = Radiobutton(master,text=val[0],variable=self.rbState,
                                           value=val[1],command=self.hideUnhideButtons)
                    self.rb.grid(row=ind+2,columnspan=2,sticky=W)
                
                self.buttonFrame = Frame(master)
                self.buttonFrame.grid(row=7,columnspan=12,sticky=W)
                
                self.addBtn = Button(self.buttonFrame,text="Add Step",command=self.addStep)
                self.addSubBtn = Button(self.buttonFrame,text="Add Sub Step",command=self.addSubStep)
                self.removeBtn = Button(self.buttonFrame,text="Remove Step",command=self.deleteStep)
                
                self.stepButtonList = [self.addBtn,self.addSubBtn,self.removeBtn]
                
                for ind,butt in enumerate(self.stepButtonList):
                    butt.grid(row=2,column=ind*4,columnspan=4,sticky=W)
                
                Label(self.buttonFrame,text="Freq:").grid(row=0,column=0,columnspan=3,sticky=W)
                Label(self.buttonFrame,text="PW:").grid(row=0,column=6,columnspan=3,sticky=W)
                Label(self.buttonFrame,text="Repeat:").grid(row=1,column=0,columnspan=3,sticky=W)
                
                self.FreqEntry = Entry(self.buttonFrame)
                self.PWEntry = Entry(self.buttonFrame)
                self.RepeatEntry = Entry(self.buttonFrame)
                
                self.FreqEntry.grid(row=0,column=3,columnspan=3)
                self.PWEntry.grid(row=0,column=9,columnspan=3)
                self.RepeatEntry.grid(row=1,column=3,columnspan=3)
                
                self.cbState = IntVar()
                self.cb = Checkbutton(self.buttonFrame,text="Bipolar?",variable=self.cbState)
                self.cb.grid(row=1,column=6,columnspan=6,sticky=W)
                self.cbState.set(0)
                
                self.stepTree = ttk.Treeview(self.buttonFrame,height=5)
                self.stepTree.grid(row=3,columnspan=12,sticky=N+S+E+W)
                
                self.stepScroll = ttk.Scrollbar(self.buttonFrame,orient="vertical",command=self.stepTree.yview)
                self.stepScroll.grid(row=3,column=12,sticky=E+N+S)
                self.stepTree.configure(yscrollcommand=self.stepScroll.set)
                
                self.stepTree["columns"] = ("one")
                self.stepTree.heading("#0",text="Steps",anchor=W)
                self.stepTree.heading("one",text="Mins (Secs)",anchor=W)
                self.treeCount = 1
                self.stepList = list()
                
                for inder, steppee in enumerate(currSteps):
                    if ',' in steppee:
                        repeats = int((steppee.split('us, '))[1].split(' times')[0])
                        stepper = self.stepTree.insert("","end",text=steppee,
                                                       value="{:0.2f}({})".format(float(repeats)/60,repeats))
                    else:
                        superRepeats = int((steppee.split('). '))[1].split(' times')[0])
                        subTexts = list()
                        subVals = list()
                        repeatSum = 0
                        for subbee in currSubSteps[inder]:
                            repeats = int((subbee.split('us, '))[1].split(' times')[0])
                            subTexts.append(subbee)
                            subVals.append(repeats)
                            repeatSum+=repeats
                        stepper = self.stepTree.insert("","end",text=steppee,
                                                       value="{:0.2f}({})".format((float(repeatSum)*float(superRepeats))/60,float(repeatSum)*float(superRepeats)))
                        for indeeez, substeps in enumerate(subTexts):
                            self.stepTree.insert(stepper,"end",text=substeps,
                                                 value="{:0.2f}({})".format(float(subVals[indeeez])/60,subVals[indeeez]))
                
                self.currSteps = currSteps
                self.curSubStep = currSubSteps
                
                if self.rbState.get() != '(255, 0, 0)':
                        self.buttonFrame.grid_remove()
                return self.e1
            
            def addStep(self,event=None):
                freq = self.FreqEntry.get()
                PW = self.PWEntry.get()
                repeat = self.RepeatEntry.get()
                
                if (len(freq)>0 and len(PW)>0 and len(repeat)>0):
                    step = self.stepTree.insert("","end",
                                                text="{}). {}Hz, {}us, {} times".format(len(self.stepTree.get_children())+1,freq,PW,repeat),
                                                value="{:0.2f}({})".format(float(repeat)/60,repeat))
                    self.stepList.append(step)
                    self.treeCount+=1
                    
                elif (len(freq)==0 and len(PW)==0 and len(repeat)>0):
                    step = self.stepTree.insert("","end",
                                                text="{}). {} times".format(len(self.stepTree.get_children())+1,repeat))
                    self.stepList.append(step)
                    self.treeCount+=1
            def addSubStep(self,event=None):
                freq = self.FreqEntry.get()
                PW = self.PWEntry.get()
                repeat = self.RepeatEntry.get()
                selectedItem = self.stepTree.selection()
                textee = self.stepTree.item(selectedItem)["text"]
                superRepeats = int((textee.split('). '))[1].split(' times')[0])
                
                if len(freq)>0 and len(PW)>0 and len(repeat)>0 and len(selectedItem)>0:
                    self.stepTree.item(selectedItem,
                                       text=textee,
                                       value="{:0.2f}({})".format((float(superRepeats)*float(repeat))/60,float(superRepeats)*float(repeat)))
                    substep = self.stepTree.insert(selectedItem,"end",
                                                   text="{}). {}Hz, {}us, {} times".format(len(self.stepTree.get_children(selectedItem))+1,freq,PW,repeat),
                                                   value="{:0.2f}({})".format(float(repeat)/60,repeat))
                    
            def deleteStep(self,event=None):
                selectedItem = self.stepTree.selection()
                if len(selectedItem)>0:
                    self.stepTree.delete(selectedItem)
                    
                    
            def hideUnhideButtons(self,event=None):
#                 if self.rbState.get=='(255, 0, 0)':
                if self.rbState.get() != '(255, 0, 0)':
                    self.buttonFrame.grid_remove()
                else:
                    self.buttonFrame.grid()
            def ok(self,event=None):
                if not self.validate():
                    self.initial_focus.focus_set()
                    return
                    
                self.withdraw()
                self.update_idletasks()
                
#                 for inder,steps in enumerate(self.currSteps):
#                     stepper = self.stepTree.insert("","end",text=steps)
#                     for substeps in self.currSubSteps[inder]:
#                         self.stepTree.insert(stepper,"end",text=substeps)
                
                self.apply()
                self.cancel()
            def cancel(self,event=None):
                self.parent.focus_set()
                self.destroy()
            def apply(self):
                portName = self.e1.get()
                shortPortName = self.e2.get()
                rbState = self.rbState.get()
                treeSteps = list()
                treeSubSteps = list()
                for steps in self.stepTree.get_children():
                    treeSteps.append(self.stepTree.item(steps)["text"])
                    tempSubs = list()
                    for subSteps in self.stepTree.get_children(steps):
                        tempSubs.append(self.stepTree.item(subSteps)["text"])
                    treeSubSteps.append(tempSubs)
                self.result = portName,shortPortName,rbState,treeSteps,treeSubSteps
            
        class KeyDialog(tk.simpledialog.Dialog):
            def buttonbox(self):
                box = Frame(self) 
                w = Button(box,text="OK",width=10,command=self.ok,default=ACTIVE)
                w.pack(side=BOTTOM,padx=5,pady=5)                
                self.bind("<Return>",self.ok)
                box.pack()
            def body(self,master):
                global ind,name,keyRow
                Label(master,text="Enter a name for this port:").grid(row=0,sticky=W)
                Label(master,text="Enter a 4-character shorthand:").grid(row=1,sticky=W)
                longName = name
                shortName = name
                self.e1 = Entry(master)
                self.e2 = Entry(master)
                                
                self.e1.insert(END,longName)
                self.e2.insert(END,shortName)
                
                self.e1.grid(row=0,column=1)
                self.e2.grid(row=1,column=1)
                return self.e1
            def ok(self,event=None):
                if not self.validate():
                    self.initial_focus.focus_set()
                    return
                    
                self.withdraw()
                self.update_idletasks()
                    
                self.apply()
                self.cancel()
            def cancel(self,event=None):
                self.parent.focus_set()
                self.destroy()
            def apply(self):
                portName = self.e1.get()
                shortPortName = self.e2.get()
                self.result = portName,shortPortName
                
        w = 400
        h = 400
        bS = 8
        
        saveCheck = 0
        
        keyRow = list()
        keyRowSave = list()
        keyRowFill = keyRowSave.copy()
        leftRow = ['3.3V','IO2','IO3','IO4','GND','IO17','IO27','IO22','3.3V',
                   'IO10','IO9','IO11','GND','DNC','IO5','IO6','IO13','IO19',
                   'IO26','GND']
        leftRowSave = leftRow.copy()
        leftRowFill = [(0,0,255)]+[(0,0,0)]*3+[(19,69,139)]+[(0,0,0)]*3+[(0,0,255)]+[(0,0,0)]*3+[(19,69,139)]*2+[(0,0,0)]*5+[(19,69,139)]
        leftRowBorder = [(255,255,255)]*20
        leftRowSteps = [[] for i in range(20)]
        leftRowSubSteps = [[] for i in range(20)]
        
        rightRow = ['5V','5V','GND','IO14','IO15','IO18','GND','IO23','IO24',
                   'GND','IO25','IO8','IO7','DNC','GND','IO12','GND','IO16',
                   'IO20','IO21']
        rightRowSave = rightRow.copy()
        rightRowFill = [(0,0,255)]*2+[(19,69,139)]+[(0,0,0)]*3+[(19,69,139)]+[(0,0,0)]*2+[(19,69,139)]+[(0,0,0)]*3+[(19,69,139)]*2+[(0,0,0)]+[(19,69,139)]+[(0,0,0)]*3
        rightRowBorder = [(255,255,255)]*20
        rightRowSteps = [[] for i in range(20)]
        rightRowSubSteps = [[] for i in range(20)]
        
        stepListCounter = 0
        for i in range(len(self.IONameList)):
            if self.IOTypeList[i] == 0:
                keyRow.append(self.IONameList[i])
                keyRowFill.append((0, 255, 0))
            elif self.IOTypeList[i] == 1:
                trueInd = i-len(keyRow)
                if 'IO{}'.format(self.GPIOList[trueInd]) in leftRow:
                    GPInd = leftRow.index('IO{}'.format(self.GPIOList[trueInd]))
                    leftRow[GPInd] = self.IONameList[i]
                    leftRowFill[GPInd] = (0, 255, 0)
                if 'IO{}'.format(self.GPIOList[trueInd]) in rightRow:
                    GPInd = rightRow.index('IO{}'.format(self.GPIOList[trueInd]))
                    rightRow[GPInd] = self.IONameList[i]
                    rightRowFill[GPInd] = (0, 255, 0)
            elif self.IOTypeList[i] == 2:
                trueInd = i-len(keyRow)
                if 'IO{}'.format(self.GPIOList[trueInd]) in leftRow:
                    GPInd = leftRow.index('IO{}'.format(self.GPIOList[trueInd]))
                    leftRow[GPInd] = self.IONameList[i]
                    leftRowFill[GPInd] = (255, 0, 0)
                    leftRowSteps[GPInd] = self.StepList[stepListCounter]
                    leftRowSubSteps[GPInd] = self.SubStepList[stepListCounter]
                    stepListCounter+=1
                if 'IO{}'.format(self.GPIOList[trueInd]) in rightRow:
                    GPInd = rightRow.index('IO{}'.format(self.GPIOList[trueInd]))
                    rightRow[GPInd] = self.IONameList[i]
                    rightRowFill[GPInd] = (255, 0, 0)
                    if self.IONameList[i] != 'Cam1':
                        rightRowSteps[GPInd] = self.StepList[stepListCounter]
                        rightRowSubSteps[GPInd] = self.SubStepList[stepListCounter]
                        stepListCounter+=1
            elif self.IOTypeList[i] == 3:
                trueInd = i-len(keyRow)
                if 'IO{}'.format(self.GPIOList[trueInd]) in leftRow:
                    GPInd = leftRow.index('IO{}'.format(self.GPIOList[trueInd]))
                    leftRow[GPInd] = self.IONameList[i]
                    leftRowFill[GPInd] = (255, 255, 0)
                if 'IO{}'.format(self.GPIOList[trueInd]) in rightRow:
                    GPInd = rightRow.index('IO{}'.format(self.GPIOList[trueInd]))
                    rightRow[GPInd] = self.IONameList[i]
                    rightRowFill[GPInd] = (255, 255, 0)
            elif self.IOTypeList[i] == 4:
                trueInd = i-len(keyRow)
                if 'IO{}'.format(self.GPIOList[trueInd]) in leftRow:
                    GPInd = leftRow.index('IO{}'.format(self.GPIOList[trueInd]))
                    leftRow[GPInd] = self.IONameList[i]
                    leftRowFill[GPInd] = (0, 255, 255)
                if 'IO{}'.format(self.GPIOList[trueInd]) in rightRow:
                    GPInd = rightRow.index('IO{}'.format(self.GPIOList[trueInd]))
                    rightRow[GPInd] = self.IONameList[i]
                    rightRowFill[GPInd] = (0, 255, 255)
                    
        def buttonHandler(event,x,y,flags,params):
            global w,h,bS,leftRow,leftRowFill,leftRowBorder
            global rightRow,rightRowFill,rightRowBorder,sided
            global ind,name,keyRow,keyRowFill,keyRowSave, saveCheck
            global leftRowSteps,leftRowSubSteps
            global rightRowSteps,rightRowSubSteps
            if event==cv2.EVENT_LBUTTONDOWN and x>(3*w//4-2*bS) and x<3*w//4-bS:
                sided = 0
                for ind,name in enumerate(leftRow):
                    if y>(30+(2*bS*ind)) and y<(30+bS+(2*bS*ind)) and ind not in [0,4,8,12,13,19]:
                        save = ind
                        GPIOWindow = tk.Tk()
                        d = GPIODialog(GPIOWindow)
                        [portName,shortPortName,rbState,treeSteps,treeSubSteps] = d.result
                        leftRowFill[save] = ast.literal_eval(rbState)
                        leftRow[save] = shortPortName
                        leftRowSteps[save] = treeSteps
                        leftRowSubSteps[save] = treeSubSteps
                        GPIOWindow.destroy()
            elif event==cv2.EVENT_LBUTTONDOWN and x>(3*w//4+bS) and x<3*w//4+2*bS:
                sided = 1
                for ind,name in enumerate(rightRow):
                    if y>(30+(2*bS*ind)) and y<(30+bS+(2*bS*ind)) and ind not in [0,1,2,3,6,9,13,14,16]:
                        save = ind
                        GPIOWindow = tk.Tk()
                        d = GPIODialog(GPIOWindow)
                        [portName,shortPortName,rbState,treeSteps,treeSubSteps] = d.result
                        rightRowFill[save] = ast.literal_eval(rbState)
                        rightRow[save] = shortPortName
                        rightRowSteps[save] = treeSteps
                        rightRowSubSteps[save] = treeSubSteps
                        GPIOWindow.destroy()
            elif event==cv2.EVENT_LBUTTONDOWN and x>(w//4-30) and x<w//4+60 and y>30 and y<60:
                if x<w//4+10:
                    if len(keyRow)<9:
                        keyRow.append('Key{}'.format(len(keyRow)+1))
                        keyRowFill.append((0, 255, 0))
                elif x>w//4+10:
                    if len(keyRow)>0 and len(keyRow)<10:
                        keyRow.remove(keyRow[-1])
                        keyRowFill.remove((0, 255, 0))
                keyRowSave = keyRow.copy()
            elif event==cv2.EVENT_LBUTTONDOWN and x>(w//4-23+bS) and x<(w//4-23+2*bS) and y>70:
                for ind,name in enumerate(keyRow):
                    if y>(70+(2*bS*ind)) and y<(70+bS+(2*bS*ind)):
                        save = ind
                        keyWindow = tk.Tk()
                        d = KeyDialog(keyWindow)
                        [portName,shortPortName] = d.result
                        keyRow[save] = shortPortName
                        keyWindow.destroy()
            elif event==cv2.EVENT_LBUTTONDOWN and x>(w//4-30) and x<(w//4+60) and y>h-90 and y<h-60:
                saveCheck = 1
            
        cv2.namedWindow('chooseGPIO')
        cv2.setMouseCallback('chooseGPIO',buttonHandler)
        while True:
            ioOutput = np.zeros((h,w,3),'uint8')
            cv2.putText(ioOutput,'Keyboard Inputs',
                        (w//4-50,20),
                            cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
            cv2.putText(ioOutput,'External I/O',
                        (3*w//4-50,20),
                        cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
            cv2.rectangle(ioOutput,(w//4-30,30),
                        (w//4+10,60),
                        (100,100,100),
                        -1)
            cv2.rectangle(ioOutput,(w//4-30,30),
                        (w//4+10,60),
                        (255,255,255),
                        1)
            cv2.putText(ioOutput,'Add',
                        (w//4-20,48),
                        cv2.FONT_HERSHEY_SIMPLEX,.35,(255,255,255),1)
            cv2.rectangle(ioOutput,(w//4+20,30),
                        (w//4+60,60),
                        (100,100,100),
                        -1)
            cv2.rectangle(ioOutput,(w//4+20,30),
                        (w//4+60,60),
                        (255,255,255),
                        1)
            cv2.putText(ioOutput,'Del',
                        (w//4+30,48),
                        cv2.FONT_HERSHEY_SIMPLEX,.35,(255,255,255),1)
            cv2.rectangle(ioOutput,(w//4-30,h-90),
                        (w//4+60,h-60),
                        (100,100,100),
                        -1)
            cv2.rectangle(ioOutput,(w//4-30,h-90),
                        (w//4+60,h-60),
                        (255,255,255),
                        1)
            cv2.putText(ioOutput,'Save',
                        (w//4-7,h-70),
                        cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),1)
            for ind,name in enumerate(keyRow):
                cv2.rectangle(ioOutput,(w//4-23+bS,70+(2*bS*ind)),
                              (w//4-23+2*bS,70+bS+(2*bS*ind)),
                              keyRowFill[ind],
                              -1)
                cv2.rectangle(ioOutput,(w//4-23+bS,70+(2*bS*ind)),
                              (w//4-23+2*bS,70+bS+(2*bS*ind)),
                              (255,255,255),
                              1)
                cv2.putText(ioOutput,name,
                        (w//4-23+bS+10,70+bS+(2*bS*ind)),
                            cv2.FONT_HERSHEY_SIMPLEX,.4,(255,255,255),1)
            for ind,name in enumerate(leftRow):
                cv2.rectangle(ioOutput,(3*w//4-2*bS,30+(2*bS*ind)),
                              (3*w//4-bS,30+bS+(2*bS*ind)),
                              leftRowFill[ind],
                              -1)
                cv2.rectangle(ioOutput,(3*w//4-2*bS,30+(2*bS*ind)),
                              (3*w//4-bS,30+bS+(2*bS*ind)),
                              leftRowBorder[ind],
                              1)
                cv2.putText(ioOutput,name,
                        (3*w//4-50,30+bS+(2*bS*ind)),
                            cv2.FONT_HERSHEY_SIMPLEX,.4,(255,255,255),1)
            for ind,name in enumerate(rightRow):
                cv2.rectangle(ioOutput,(3*w//4+bS,30+(2*bS*ind)),
                              (3*w//4+2*bS,30+bS+(2*bS*ind)),
                              rightRowFill[ind],
                              -1)
                cv2.rectangle(ioOutput,(3*w//4+bS,30+(2*bS*ind)),
                              (3*w//4+2*bS,30+bS+(2*bS*ind)),
                              rightRowBorder[ind],
                              1)
                cv2.putText(ioOutput,name,
                        (3*w//4+bS+10,30+bS+(2*bS*ind)),
                            cv2.FONT_HERSHEY_SIMPLEX,.4,(255,255,255),1)
            cv2.imshow('chooseGPIO',ioOutput)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if saveCheck==1:
                IONameList = keyRow.copy()
                IOTypeList = [0] * len(keyRow)
                GPIOList = list()
                StepList = list()
                SubStepList = list()
                
                for i in range(len(leftRow)):
                    if leftRowFill[i] == (255, 0, 0):
                        IONameList.append(leftRow[i])
                        IOTypeList.append(2)
                        GPIOList.append(int(leftRowSave[i][2:]))
                        StepList.append(leftRowSteps[i])
                        SubStepList.append(leftRowSubSteps[i])
                    elif leftRowFill[i] == (0, 255, 0):
                        IONameList.append(leftRow[i])
                        IOTypeList.append(1)
                        GPIOList.append(int(leftRowSave[i][2:]))
                    elif leftRowFill[i] == (255, 255, 0):
                        IONameList.append(leftRow[i])
                        IOTypeList.append(3)
                        GPIOList.append(int(leftRowSave[i][2:]))
                    elif leftRowFill[i] == (0, 255, 255):
                        IONameList.append(leftRow[i])
                        IOTypeList.append(4)
                        GPIOList.append(int(leftRowSave[i][2:]))
                    if rightRowFill[i] == (255, 0, 0):
                        IONameList.append(rightRow[i])
                        IOTypeList.append(2)
                        GPIOList.append(int(rightRowSave[i][2:]))
                        if rightRow[i] != 'Cam1':
                            StepList.append(rightRowSteps[i])
                            SubStepList.append(rightRowSubSteps[i])
                    elif rightRowFill[i] == (0, 255, 0):
                        IONameList.append(rightRow[i])
                        IOTypeList.append(1)
                        GPIOList.append(int(rightRowSave[i][2:]))
                    elif rightRowFill[i] == (255, 255, 0):
                        IONameList.append(rightRow[i])
                        IOTypeList.append(3)
                        GPIOList.append(int(rightRowSave[i][2:]))
                    elif rightRowFill[i] == (0, 255, 255):
                        IONameList.append(rightRow[i])
                        IOTypeList.append(4)
                        GPIOList.append(int(rightRowSave[i][2:]))
                self.IONameList = IONameList
                self.IOTypeList = IOTypeList
                self.GPIOList = GPIOList
                self.StepList = StepList
                print(StepList)
                print(len(StepList))
                self.SubStepList = SubStepList
                break
            
        cv2.destroyAllWindows()
        self.grab_set()
        
    def validate(self):
        return 1
        
    def apply(self):
        pass