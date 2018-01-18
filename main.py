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
import os

def computeSpeeds(x, y):
    scalar = 0.05 / math.sqrt(pow(x, 2) + pow(y, 2))
    speed_x = scalar * x
    speed_y = scalar * y
    return [speed_x, speed_y]             

def followWaypoints(drone, path, curPos, pointCount, targetPoint):
    if pointCount < len(path) and path[pointCount] != -1:
        pprint(curPos)
        print(pointCount)
        if abs(curPos[0] - targetPoint[0]) <= 0.1 and abs(curPos[1] - targetPoint[1]) <= 0.1:
            drone.stop()
            print("wayPoint arrived")
            if pointCount < len(path)-1:
                pointCount+=1
                targetPoint = path[pointCount]
            time.sleep(5)
        else:
            speeds = computeSpeeds(targetPoint[0]-curPos[0], targetPoint[1]-curPos[1])
            print("pointCount" + str(pointCount))
            print("speeds")
            pprint(speeds)
            drone.move(speeds[0], speeds[1], 0.0, 0.0)
            drone.stop()
            time.sleep(0.5)
    if path[pointCount] == -1:
        # land
        drone.land()
        print("delivery complete")
        time.sleep(5)
    return path, curPos, pointCount, targetPoint


def main():
    #path = [(0.3,0.3),(0.6,0),(0.9,0.3),(1.2,0.3),(1.2,0.6),(1.5,0.6),-1]
    path = [(0.3,0.3),(1.8,0.3),-1]

    # tag id with positions
    tags = {"0":(0,0), "1":(0.3,0), "2":(0.6,0), "3":(0.9,0), "4":(1.2,0), "5":(1.5,0), "6":(1.8,0),
        "7":(0,0.3), "8":(0.3,0.3), "9":(0.6,0.3),  "10":(0.9,0.3), "11":(1.2,0.3), "12":(1.5,0.3), "13":(1.8,0.3),
        "14":(0,0.6), "15":(0.3,0.6), "16":(0.6,0.6), "17":(0.9,0.6), "18":(1.2,0.6), "19":(1.5,0.6), "20":(1.8,0.6),
        "21":(0,0.9), "22":(0.3,0.9), "23":(0.6,0.9), "24":(0.9,0.9), "25":(1.2,0.9), "26":(1.5,0.9), "27":(1.8,0.9)}

    # drone's current position, count and point
    curPos = (0.3,0.3)
    pointCount = 0
    targetPoint = path[0]
    isSpeedComputed = False
    curSpeeds = None

    # init drone 
    drone = ps_drone.Drone()
    drone.startup()

    drone.reset()
    while (drone.getBattery()[0] == -1):
        time.sleep(0.1)
    print("Battery: " + str(drone.getBattery()[0]) + "%  " + str(drone.getBattery()[1]))
    drone.setConfigAllID()
    drone.sdVideo()
    drone.groundCam()
    drone.stopVideo()

    # init video
    #video = subprocess.Popen(['apriltags/build/bin/drone_demo', '-D', '-1', '-c'], stdout=subprocess.PIPE)
    video = subprocess.Popen(['apriltags/build/bin/drone_demo', '-D', '-1','-c','-s','3'], stdout=subprocess.PIPE)
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
        key = drone.getKey()
        if key == " ":
             drone.land()
        # get detection data
        if video.poll() is None:
            raw = video.stdout.readline()
            if raw.startswith('#'):
                detection = json.loads(raw[1:])
        else:
            video = subprocess.Popen(['apriltags/build/bin/drone_demo', '-D', '-1','-c','-s','3'], stdout=subprocess.PIPE)
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
                curPos = (point[0] - dist_x, point[1] + dist_y)
		#pprint(curPos)
                path, curPos, pointCount, targetPoint = followWaypoints(drone, path, curPos, pointCount, targetPoint)
        #else:
        #    drone.land()
        #    print("land...")

main()

