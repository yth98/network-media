# Ref: https://github.com/davisking/dlib/blob/master/python_examples/face_landmark_detection.py

# set_image(self: dlib.image_window, image: object)
# add_overlay(self: dlib.image_window, rectangles: dlib.rectangles, color: dlib.rgb_pixel=rgb_pixel(255,0,0))
# add_overlay(self: dlib.image_window, detection: dlib.full_object_detection, color: dlib.rgb_pixel=rgb_pixel(0,0,255))

import cv2
import dlib
import time
import numpy
from PIL import Image


time.clock()
ts=time.clock()

if(__name__=='__main__'): pass
else:
    global face, face_proc
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
    print("FACE Init time:",time.clock()-ts,"s")

    def face(img):
        if type(img) is str:
            img = cv2.imread(img)
            if img is None: return None
            d_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            d_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        dets = detector(d_img, 1) # dlib.dlib.rectangles
        if(not len(dets)): return None

        #win = dlib.image_window()
        #win.set_image(d_img)
        #win.add_overlay(dets)

        for k, d in enumerate([dets[0]]):   # dlib.dlib.rectangle
            #print("Detection {}: Left: {} Top: {} Right: {} Bottom: {}".format(k, d.left(), d.top(), d.right(), d.bottom()))

            shape = predictor(img, d)       # dlib.dlib.full_object_detection
            if(shape.num_parts != 68): break
            for i in range(shape.num_parts): #print("Part {}: {}".format(i+1,shape.part(i)))
                pass

            #win.clear_overlay()
            #win.add_overlay(shape,dlib.rgb_pixel(0,255,0))
            #win.add_overlay(shape.rect,dlib.rgb_pixel(0,0,0))

        #dlib.hit_enter_to_continue()
        pt = []
        for i in range(68):
            pt.append((shape.part(i).x,shape.part(i).y))
        return [(dets[0].left(), dets[0].top()), (dets[0].right(), dets[0].bottom()), pt]

    def face_proc(pix):
        rect = face(pix)
        pix = numpy.zeros((*(pix.shape[0:2]),3), numpy.uint8)
        if(not rect is None):
            cv2.rectangle(pix, *(rect[0:2]), (0,0,255))
            for i in range(0,16):
                cv2.line(pix, rect[2][i], rect[2][i+1], (255,0,0))
            for i in range(17,21):
                cv2.line(pix, rect[2][i], rect[2][i+1], (255,255,0))
            for i in range(22,26):
                cv2.line(pix, rect[2][i], rect[2][i+1], (255,255,0))
            for i in range(27,30):
                cv2.line(pix, rect[2][i], rect[2][i+1], (255,0,0))
            for i in range(31,35):
                cv2.line(pix, rect[2][i], rect[2][i+1], (255,0,0))
            for i in range(36,41):
                cv2.line(pix, rect[2][i], rect[2][i+1], (128,255,0))
            for i in range(42,47):
                cv2.line(pix, rect[2][i], rect[2][i+1], (128,255,0))
            for i in range(48,67):
                cv2.line(pix, rect[2][i], rect[2][i+1], (0,255,0))
        return pix
'''
cv2.namedWindow("wind")
#print(face("../src/people_bunch.jpg"))
cap = cv2.VideoCapture(0)
while True:
    ts = time.clock()
    pix = cv2.VideoCapture.read(cap)[1]
    pix = cv2.resize(pix, (300,225), fx=0.4, fy=0.4) 
    rect = face(pix)
    print(time.clock() - ts, "s")
    if(not rect is None):
        cv2.rectangle(pix, *(rect[0:2]), (0,0,255))
        for i in range(0,16):
            cv2.line(pix, rect[2][i], rect[2][i+1], (255,0,0))
        for i in range(17,21):
            cv2.line(pix, rect[2][i], rect[2][i+1], (255,255,0))
        for i in range(22,26):
            cv2.line(pix, rect[2][i], rect[2][i+1], (255,255,0))
        for i in range(27,30):
            cv2.line(pix, rect[2][i], rect[2][i+1], (255,0,0))
        for i in range(31,35):
            cv2.line(pix, rect[2][i], rect[2][i+1], (255,0,0))
        for i in range(36,41):
            cv2.line(pix, rect[2][i], rect[2][i+1], (128,255,0))
        for i in range(42,47):
            cv2.line(pix, rect[2][i], rect[2][i+1], (128,255,0))
        for i in range(48,67):
            cv2.line(pix, rect[2][i], rect[2][i+1], (0,255,0))
    cv2.imshow("wind", pix) # (BGR)
    cv2.waitKey(5)
cap.release()
'''
