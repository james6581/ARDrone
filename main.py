#!/usr/bin/env python
from __future__ import print_function
from pprint import pprint
from subprocess import PIPE, Popen
from threading  import Thread
from Queue import Queue, Empty
import time, sys
import ps_drone
import cv2
import json
import numpy
import math
import os
import signal


def tick(sec):
    t0 = time.time()
    diff = 0.0
    while diff < sec:
        diff = time.time() - t0

def computeSpeeds(x, y):
    scalar = 0.05 / math.sqrt(pow(x, 2) + pow(y, 2))
    speed_x = scalar * x
    speed_y = scalar * y
    return [speed_x, speed_y]             

def moveToTargetPoint(drone, path, curPos, pointCount, targetPoint):
    if pointCount < len(path) and path[pointCount] != -1:
        pprint(curPos)
        print(pointCount)
        if abs(curPos[0] - targetPoint[0]) <= 0.1 and abs(curPos[1] - targetPoint[1]) <= 0.1:
            drone.stop()
            print("targetPoint arrived")
            if pointCount < len(path)-1:
                pointCount+=1
                targetPoint = path[pointCount]
        else:
            speeds = computeSpeeds(targetPoint[0]-curPos[0], targetPoint[1]-curPos[1])
            print("pointCount" + str(pointCount))
            print("speeds")
            pprint(speeds)
            drone.move(speeds[1], speeds[0], 0.0, 0.0)
            #tick(0.5)
            #drone.stop()
            #tick(0.5)
            #time.sleep(1)
            #drone.stop()
            #time.sleep(0.3)
    if path[pointCount] == -1:
        # land
        drone.land()
        print("delivery complete")
        #time.sleep(5)
    return path, curPos, pointCount, targetPoint

def getCurPosfromTag(detectedTag,tags):
    tagID = detectedTag["id"]
    tagPos = tags[str(tagID)]
    distX = detectedTag["dist_z"]
    distY = detectedTag["dist_y"]
    curPos = (tagPos[0] - distX, tagPos[1] + distY)
    return curPos
	
def getCurPosfromTags(detectedTags,tags):
    tempX = 0
    tempY = 0
    numDetectedTags = len(detectedTags)

    for detectedTag in detectedTags["tags"]:
        curPos = getCurPosfromTag(detectedTag,tags)
        tempX += curPos[0]
        tempY += curPos[1]
    
    calibratedX = tempX / numDetectedTags
    calibratedY = tempY / numDetectedTags
    
    return (calibratedX, calibratedY)

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def main():
    #path = [(0.3,0.3),(0.6,0),(0.9,0.3),(1.2,0.3),(1.2,0.6),(1.5,0.6),-1]
    path = [(0.3,0.3),(1.5,0.3),-1]

    # tag id with positions
    tags = {"0":(0,0), "1":(0.3,0), "2":(0.6,0), "3":(0.9,0), "4":(1.2,0), "5":(1.5,0), "6":(1.8,0),
        "7":(0,0.3), "8":(0.3,0.3), "9":(0.6,0.3),  "10":(0.9,0.3), "11":(1.2,0.3), "12":(1.5,0.3), "13":(1.8,0.3),
        "14":(0,0.6), "15":(0.3,0.6), "16":(0.6,0.6), "17":(0.9,0.6), "18":(1.2,0.6), "19":(1.5,0.6), "20":(1.8,0.6),
        "21":(0,0.9), "22":(0.3,0.9), "23":(0.6,0.9), "24":(0.9,0.9), "25":(1.2,0.9), "26":(1.5,0.9), "27":(1.8,0.9)}

    # drone's current position, point count, target point, and detection
    curPos = (0.0,0.0)
    pointCount = 0
    targetPoint = path[0]
    detection = {'tags': []}

    # init drone 
    drone = ps_drone.Drone()
    drone.startup()

    drone.reset()
    while (drone.getBattery()[0] == -1):
        time.sleep(0.1)
    print("Battery: " + str(drone.getBattery()[0]) + "%  " + str(drone.getBattery()[1]))
    drone.useDemoMode(True)    
    drone.setConfigAllID()
    drone.sdVideo()
    drone.groundCam()
    drone.stopVideo()

    ON_POSIX = 'posix' in sys.builtin_module_names

    video = Popen(['apriltags/build/bin/drone_demo', '-D', '-1','-c','-s','3'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
    q = Queue()
    t = Thread(target=enqueue_output, args=(video.stdout, q))
    t.daemon = True
    t.start()
    detection = {'tags': []}

    # show frame
    image = numpy.zeros((360, 640))
    cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
    cv2.imshow('image', image)
	
    # take off
    print("taking off...")
    drone.takeoff()
    time.sleep(15)
    
	# loop
    for count in range(10000):
        
        # manual control of landing for safety
        key = drone.getKey()
        if key == " ":
             drone.land()

        if video.poll() is None:
            try:  
                raw = q.get_nowait()
            except Empty:
                print('no output yet')
            else:
                if raw.startswith('#'):
                    detection = json.loads(raw[1:])
        else:
            video = Popen(['apriltags/build/bin/drone_demo', '-D', '-1','-c','-s','3'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
            detection = {'tags': []}
            drone.hover()
        
        # calculate current position from detected tags
        if 'image' in detection and len(detection['tags']):
            curPos = getCurPosfromTags(detection, tags)
            #pprint(curPos)
        else:
            drone.stop()
        #cv2.waitKey(500)
        # move to the target point
        path, curPos, pointCount, targetPoint = moveToTargetPoint(drone, path, curPos, pointCount, targetPoint)

main()

