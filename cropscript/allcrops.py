from __future__ import division
import cv2
import os
import json
import numpy as np
import sys
import pickle


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


def get_flow(flow_dir, num):
    name = str(num) + "_" + str(num + 1) + ".flo"
    with open(os.path.join(flow_dir, name), 'rb') as f:
        np.fromfile(f, np.int32, 1).squeeze()
        width = np.fromfile(f, np.int32, 1).squeeze()
        height = np.fromfile(f, np.int32, 1).squeeze()
        flow = np.fromfile(f, np.float32, width * height * 2).reshape(
            (height, width, 2))
        flow = flow.transpose(2, 0, 1)
        
        cur_flow = np.array(flow, dtype=np.float16)
        __max = np.max(cur_flow)
        __min = np.min(cur_flow)
        cur_flow = (cur_flow - __min) * 255 / (__max - __min)
        cur_flow = cur_flow.astype(np.uint8)
        cur_flow = cur_flow.transpose(1, 2, 0)
        
        return cur_flow
    raise "Can't open"+os.path.join(flow_dir, name)


def get_frame(path, num):
    fr = os.path.join(path, str(num) + '.png')
    return cv2.imread(fr)


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


def create_crops():
    truth_path = '/usr0/home/schakra1/research/truth/0072.json'
    vidname = "vid_0072"
    path_frames = "/usr0/home/mpetrovi/dataset/computedFlow/allFlows/" + \
                  vidname + "/frames"
    path_flows = "/usr0/home/mpetrovi/dataset/computedFlow/allFlows/" + \
                 vidname + "/flows"
    truth = json.load(open(truth_path))
    boxes = create_tracks(truth)
    targetsave = './crops/vid_0072/target'
    searchsave = './crops/vid_0072/searching'
    
    strings = []
    print "Vid 0072"
    frames = sorted([int(x.split('.')[0]) for x in os.listdir(path_frames)])
    for i in range(len(frames)-2):  # Dont know how to end
        pint("Frame n: " + str(i))
        #  target is the actual frame
        #  we want to search this frame in
        #  the frame just after
        frame_target, flow_target = frames[i], frames[i]
        frame_search, flow_search = frames[i+1], frames[i+1]
        
        for obj in boxes.keys():
            btarget = boxes[obj][frame_target]
            bsearch = boxes[obj][frame_search]
            if len(bsearch) == 0:
                print "Annotation not found, try the one just before"
                bsearch = btarget
                if len(bsearch) == 0:
                    print "The one before doesnt work too .."
            
            imframetarget = get_frame(path_frames, frame_target)
            imframesearch = get_frame(path_frames, frame_search)
            imflowtarget = get_flow(path_flows, flow_target)
            imflowsearch = get_flow(path_flows, flow_search)
            
            imtarget = np.concatenate([imframetarget, imflowtarget], axis=2)
            imsearch = np.concatenate([imframesearch, imflowsearch], axis=2)
            
            imh, imw, _ = imtarget.shape
            print imtarget.shape
            print imtarget

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
        
            targetname = os.path.join(targetfolder, str(frame_target) + '.pkl')
            #  The name is also frame_target to have correspondance
            searchname = os.path.join(searchfolder, str(frame_target) + '.pkl')

            targetfile = open(targetname, 'wb')
            searchfile = open(searchname, 'wb')
            
            pickle.dump(imcroptarget, targetfile)
            pickle.dump(imcropsearch, searchfile)
            
            coord = get_string(targetname, searchname,
                               sx1, sx2, sy1, sy2, gx1, gx2, gy1, gy2)
            strings.append(coord)
            return 

    with open('save.txt', 'w') as f:
        f.write('\n'.join(strings))


create_crops()
