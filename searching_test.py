import os
import matplotlib
from Algorithm.main import *
import cv2
import argparse
import time
import requests
import yaml
import tqdm
import torchvision
from turtle import color
from Arm_Lib import Arm_Device
import pandas as pd
import seaborn
import numpy as np

# M1 SSL Fix to load 
# torch model
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
matplotlib.use('TKAgg')
# Disable tensorflow output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


#HERE
Arm = Arm_Device()
time.sleep(.1)
 
time_1 = 500
time_2 = 1000
time_sleep = 0.5


def center(xDegree, cap):
    #set angles that arm was at previously and create variables to be adjusted to center item on camera
    xDeg = xDegree
    yDeg = 20
    #setup computer vision
    model = get_model()
    ret, frame = cap.read()
    results = model(frame)
    dataframe = results.pandas().xyxy[0]
    isEmpty = dataframe.empty
    #make sure the frame is not empty to program does not crash
    if not isEmpty:
        #add coordinatates of border to find the coordinates of the center of the image
        xCoor = ((dataframe.iat[0,0]+dataframe.iat[0,2])/2)
        yCoor = ((dataframe.iat[0,1]+dataframe.iat[0,3])/2)
        print(dataframe.iat[0,0], " ", dataframe.iat[0,2])
        print(xCoor, " ", yCoor)
        #center the item on the horizontal axis
        while (xCoor < 305 or xCoor > 335):
            #adjust camera left or right depending on which side of the center the item is
            if xCoor > 335:
                xDeg -= 1
                Arm.Arm_serial_servo_write6(xDeg, 90, 30, yDeg, 90, 85, 10)
                time.sleep(5)
            elif xCoor < 305:
                xDeg += 1
                Arm.Arm_serial_servo_write6(xDeg, 90, 30, yDeg, 90, 85, 10)
                time.sleep(5)
            #update information from the camera
            isEmpty = dataframe.empty
            ret, frame = cap.read()
            results = model(frame)
            dataframe = results.pandas().xyxy[0]
            isEmpty = dataframe.empty
            #update coordinates
            xCoor = ((dataframe.iat[0,0]+dataframe.iat[0,2])/2)
            yCoor = ((dataframe.iat[0,1]+dataframe.iat[0,3])/2)
            #display camera on screen
            cv2.imshow('YOLO', np.squeeze(results.render()))
            
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
            print(xCoor, " ", yCoor)
        #adjust camera up and down depending on which side of the center the item is
        while (yCoor < 225 or yCoor > 255) and not isEmpty:
            if yCoor > 255:
                yDeg -= 1
                Arm.Arm_serial_servo_write6(xDeg, 90, 30, yDeg, 90, 85, 10)
                time.sleep(5)
            elif yCoor < 225:
                yDeg += 1
                Arm.Arm_serial_servo_write6(xDeg, 90, 30, yDeg, 90, 85, 10)
                time.sleep(5)
            #update camera info
            ret, frame = cap.read()
            results = model(frame)
            dataframe = results.pandas().xyxy[0]
            isEmpty = dataframe.empty
            #update coordinates
            xCoor = ((dataframe.iat[0,0]+dataframe.iat[0,2])/2)
            yCoor = ((dataframe.iat[0,1]+dataframe.iat[0,3])/2)
            #display camera on screen
            cv2.imshow('YOLO', np.squeeze(results.render()))
            
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
            print(xCoor, " ", yCoor, " ", dataframe.iat[0,4])
        #return true if able to center and false if not
        return True
    
    return False
        
            
def search(item, cap):

    xDegree = 30
    turning_right = True
#read in the data from the camera
    model = get_model()
    ret, frame = cap.read()
    results = model(frame)
    dataframe = results.pandas().xyxy[0]
    isEmpty = dataframe.empty
#set arm to beginning of sweep to search
    Arm.Arm_serial_servo_write6(30, 90,30, 20, 90, 85, 500)
#move left and right to search for the item
    while isEmpty:
        if xDegree == 30:
            xDegree += 15
            turning_right = True
            Arm.Arm_serial_servo_write6(xDegree, 90, 30,20, 90, 85, 750)
            time.sleep(5)
        elif xDegree < 150 and turning_right:
            xDegree += 15
            Arm.Arm_serial_servo_write6(xDegree, 90, 30,20, 90, 85, 750)
            time.sleep(5)
        elif xDegree > 30 and not turning_right:
            xDegree -= 15
            Arm.Arm_serial_servo_write6(xDegree, 90, 30,20, 90, 85, 750)
            time.sleep(5)
        elif xDegree == 150:
            xDegree -= 15
            turning_right = False
            Arm.Arm_serial_servo_write6(xDegree, 90, 30,20, 90, 85, 750)
            time.sleep(5)
#read in the data from the camera and update the info
        ret, frame = cap.read()
        results = model(frame)
        dataframe = results.pandas().xyxy[0]
        isEmpty = dataframe.empty
#check if its not empty and then check if it is correct item and center
    if not isEmpty:
        if dataframe.iat[0,6] == item:
            return center(xDegree, cap)
        else:
            return False

def main(_argv):

    #parser = argparse.ArgumentParser()
    # Initialize Camera Intel Realsense


    # Parse arguments
    # if _argv.Debug == "1" or _argv.D == "1":
    #    Debug_flag = 1
    #    # Create window for video
    #    cv2.namedWindow("Video")
    #    cv2.namedWindow("Video_Depth")

    # elif _argv.Debug == "0" or _argv.D == "0":
    #   Debug_flag = 0

    # Load saved CV model
    model = get_model()

    # Initialize Algorithm
    oldCords = None
    depth = None
	#HERE
    i = 90
    Arm.Arm_serial_servo_write6(i, 90, 90,20, 90, 85, 500)
    time.sleep(1)
    found = False
    while True:

        cap = cv2.VideoCapture(-1)
        while cap.isOpened():
            ret, frame = cap.read()

            # Make detections
            results = model(frame)

	    #data frame not used 
            dataframe = results.pandas().xyxy[0]
            isEmpty = dataframe.empty
            
            while not found:
                found = search("scissors", cap)

            while True:
                if not dataframe.empty:
                    print((dataframe.iat[0,0]+dataframe.iat[0,2])/2, " ", (dataframe.iat[0,1]+dataframe.iat[0,3])/2, " ", dataframe.iat[0,4])

            cv2.imshow('YOLO', np.squeeze(results.render()))
            
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
