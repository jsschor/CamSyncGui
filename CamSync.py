from ttk import *
import tkinter as tk
from tkinter import *
import cv2
from PIL import Image, ImageTk
import os
import numpy as np
import picamera
from picamera.array import PiRGBArray
import imutils
from imutils.video import VideoStream
import time

global last_frame                                      #creating global              variable
last_frame = np.zeros((480, 640, 3), dtype=np.uint8)
global last_frame2                                      #creating global      variable
last_frame2 = np.zeros((480, 640, 3), dtype=np.uint8)
global last_frameb                                      #creating global              variable
last_frameb = np.zeros((480, 640, 3), dtype=np.uint8)
global last_frameb2                                      #creating global      variable
last_frameb2 = np.zeros((480, 640, 3), dtype=np.uint8)

global cap
global cap2
cap = VideoStream(src=0).start()
cap2 = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

def show_vid():                                        #creating a function
    frame = cap.read()
    frame = cv2.resize(frame,(400,500))
    global last_frame
    last_frame = frame.copy()
    global last_frame2
    last_frame2 = frame.copy()

    pic = cv2.cvtColor(last_frame, cv2.COLOR_BGR2RGB)     #we can change the display color of the frame gray,black&white here
    img = Image.fromarray(pic)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)
    lmain.after(10, show_vid)


def show_vid2():
    frame = cap2.read()
    frame = cv2.resize(frame,(400,500))
    global last_frameb
    last_frameb = frame.copy()
    global last_frameb2
    last_frameb2 = frame.copy()

    pic = cv2.cvtColor(last_frameb2, cv2.COLOR_BGR2RGB)     #we can change the display color of the frame gray,black&white here
    img = Image.fromarray(pic)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain2.imgtk = imgtk
    lmain2.configure(image=imgtk)
    lmain2.after(10, show_vid2)

if __name__ == '__main__':
    root=tk.Tk()                                     #assigning root variable        for Tkinter as tk
    lmain = tk.Label(master=root)
    lmain2 = tk.Label(master=root)
    #lmain.Frame= Frame(width=768, height=576)
    #framex.grid(column=3,rowspan=2,padx=5, pady=5)
    lmain.pack(side = LEFT)
    lmain2.pack(side = RIGHT)
    root.title("Fire Alarm Detector")            #you can give any title
    root.geometry("900x700+100+10") #size of window , x-axis, yaxis
    exitbutton = Button(root, text='Quit',fg="red",command=   root.destroy).pack(side = BOTTOM,)
    show_vid()
#     show_vid2()
    root.mainloop()                                  #keeps the application in an infinite loop so it works continuosly
    cap.stop()
    cap2.stop()
