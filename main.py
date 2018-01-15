#!/usr/bin/env python
from __future__ import print_function
from pprint import pprint
import time, sys
import ps_drone
import cv2
import subprocess
import json
import numpy
import math

path = [(0.3,0.3),(0.6,0.6),(0.9,0.6),(1.2,0.3),(1.5,0.6),(1.8,0.6),(2.1,0.6),(2.4,0.9)]
#path = [(0.3,0),(1.5,0),(0.3,0.6)]
# tag id with positions
tags = {"0":(0,0), "1":(0.3,0), "2":(0.6,0), "3":(0.9,0), "4":(1.2,0), "5":(1.5,0), "6":(1.8,0),
        "7":(0,0.3), "8":(0.3,0.3), "9":(0.6,0.3), "10":(0.9,0.3), "11":(1.2,0.3), "12":(1.5,0.3), "13":(1.8,0.3),
        "14":(0,0.6), "15":(0.3,0.6), "16":(0.6,0.6), "17":(0.9,0.6), "18":(1.2,0.6), "19":(1.5,0.6), "20":(1.8,0.6),
        "21":(0,0.9), "22":(0.3,0.9), "23":(0.6,0.9), "24":(0.9,0.9), "25":(1.2,0.9), "26":(1.5,0.9), "27":(1.8,0.9)}

# drone's current position
global curPos
curPos = (0.3,0.3)

global curPointCount
curPointCount = 0

global curPoint
curPoint = path[0]

def computeSpeeds(v1, v2):
    v3 = [v1, v2]
    alpha = 0.05 / math.sqrt(pow(v1, 2) + pow(v2, 2))
    u1 = alpha * v1
    u2 = alpha * v2
    return [u1, u2]             

def followWaypoints():
    global curPointCount
    global curPos
    global curPoint
    while curPointCount <= len(path):
        pprint(curPos)
        if abs(curPos[0] - curPoint[0]) <= 0.3 and abs(curPos[1] - curPoint[1]) <= 0.3:
            #drone.stop()
            print("wayPoint arrived")
            #time.sleep(5)
            curPointCount+=1
            curPoint = path[curPointCount]
        else:
            speeds = computeSpeeds(curPoint[0], curPoint[1])
            print("curPointCount" + str(curPointCount))
            #print("speeds")
            #pprint(speeds)
            #drone.move(speeds[0], speeds[1], 0, 0)
    #drone.land()
        time.sleep(1)
    print("delivery complete")


def main():
	
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

    # init video
    #video = subprocess.Popen(['apriltags/build/bin/drone_demo', '-D', '-1', '-c'], stdout=subprocess.PIPE)
    video = subprocess.Popen(['apriltags/build/bin/drone_demo', '-D', '-1','-s','3'], stdout=subprocess.PIPE)
    detection = {'tags': []}

    # show frame
    image = numpy.zeros((360, 640))
    cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
    cv2.imshow('image', image)
	
    # loop
    for count in range(10000):
        # get detection data
        if video.poll() is None:
            raw = video.stdout.readline()
            if raw.startswith('#'):
                detection = json.loads(raw[1:])
        else:
            video = subprocess.Popen(['apriltags/build/bin/drone_demo', '-D', '-1','-s','3'], stdout=subprocess.PIPE)
            detection = {'tags': []}
            drone.hover()
			
        # detect tag
        ids = [tag['id'] for tag in detection['tags']]
        #print('Detect {} tags {}'.format(len(detection['tags']), ids))

        if 'image' in detection and len(detection['tags']):
            for tag in detection['tags']:
                id_tag = tag["id"]
                point = tags[str(id_tag)]
                #print(str(point))
                dist_x = tag["dist_z"]
                dist_y = tag["dist_y"]
                global curPos
                curPos = (point[0] - dist_x, point[1] + dist_y)
		#pprint(curPos)
                #followWaypoints()

main()

