from __future__ import division
import cv2
import os
import json
import numpy as np
import sys


def create_tracks(boxes):
    tracks = {}
    for i in range(len(boxes)):
        for obj in boxes[i]:
            if obj not in tracks:
                tracks[obj] = []
    for i in range(len(boxes)):
        for obj in tracks:
            if obj not in boxes[i]:
                tracks[obj].append([])
            else:
                box = boxes[i][obj]
                tracks[obj].append([box['x'], box['y'], box['w'], box['h']])
                
    return tracks


def pint(s):
    sys.stdout.write("\r%s" % s)
    sys.stdout.flush()


#  This function give the coord of the box in the crop
def get_coord(sx1, sx2, sy1, sy2, gx1, gx2, gy1, gy2):
    h, w = gy2 - gy1, gx2 - gx1
    return (sx1-gx1)/w, (sy1-gy1)/h, (-sx2+gx2)/w, (-sy2+gy2)/h


def get_string(targetname, searchname, sx1, sx2, sy1, sy2, gx1, gx2, gy1, gy2):
    c1, c2, c3, c4 = get_coord(sx1, sx2, sy1, sy2, gx1, gx2, gy1, gy2)
    lst = [targetname, searchname, str(c1), str(c2), str(c3), str(c4)]
    return ','.join(lst)


def create_jpgcrops():
    truth_path = '/usr0/home/schakra1/research/truth/0072.json'
    path = "/usr0/home/mpetrovi/dataset/computedFlow/allFlows/vid_0072/frames"
    truth = json.load(open(truth_path))
    boxes = create_tracks(truth)
    targetsave = './crops/vid_0072/target'
    searchsave = './crops/vid_0072/searching'
    
    strings = []
    print "Vid 0072"
    frames = sorted([int(x.split('.')[0]) for x in os.listdir(path)])
    for i in range(len(frames)-1):
        pint("Frame n: " + str(i))
        #  target is the actual frame
        #  we want to search this frame in
        #  the frame just after
        frame_target = frames[i]
        frame_search = frames[i+1]
        
        for obj in boxes.keys():
            btarget = boxes[obj][frame_target]
            bsearch = boxes[obj][frame_search]
            if len(bsearch) == 0:
                print "Annotation not found, try the one just before"
                bsearch = btarget
                if len(bsearch) == 0:
                    print "The one before doesnt work too .."
            
            targetframe = os.path.join(path, str(frame_target) + '.png')
            searchframe = os.path.join(path, str(frame_search) + '.png')
            
            imtarget = cv2.imread(targetframe)
            imsearch = cv2.imread(searchframe)
            imh, imw, _ = imtarget.shape
        
            x1, y1, bw, bh = btarget[0], btarget[1], btarget[2], btarget[3]
            x2, y2 = x1 + bw, y1 + bh

            sx1, sy1, sbw, sbh = bsearch[0], bsearch[1], bsearch[2], bsearch[3]
            sx2, sy2 = sx1 + sbw, sy1 + sbh
        
            marginh = bh//2
            marginw = bw//2
    
            #  box is in the center
            gx1 = max(x1 - marginw, 0)
            gy1 = max(y1 - marginh, 0)
            gx2 = min(x2 + marginw, imw)
            gy2 = min(y2 + marginh, imh)
            
            imcroptarget = imtarget[gy1:gy2, gx1:gx2]
            imcropsearch = imsearch[gy1:gy2, gx1:gx2]
            
            targetfolder = os.path.join(targetsave, obj)
            if not os.path.exists(targetfolder):
                os.makedirs(targetfolder)

            searchfolder = os.path.join(searchsave, obj)
            if not os.path.exists(searchfolder):
                os.makedirs(searchfolder)
        
            targetname = os.path.join(targetfolder, str(frame_target) + '.jpg')
            #  The name is also frame_target to have correspondance
            searchname = os.path.join(searchfolder, str(frame_target) + '.jpg')
            
            cv2.imwrite(targetname, imcroptarget)
            cv2.imwrite(searchname, imcropsearch)

            coord = get_string(targetname, searchname, sx1, sx2, sy1, sy2, gx1, gx2, gy1, gy2)
            strings.append(coord)

    with open('save.txt', 'w') as f:
        f.write('\n'.join(strings))


create_jpgcrops()
