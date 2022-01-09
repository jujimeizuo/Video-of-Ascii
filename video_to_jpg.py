#coding=utf-8
import cv2
videoFile = 'vedio.mp4'
outputFile = 'url'

vc = cv2.VideoCapture(videoFile)
print(vc)
c = 1
if vc.isOpened():
    rval, frame = vc.read()
else:
    print('open-Error!')
    rval = False

timeF = 100  #视频帧计数间隔次数
while rval:
    print("ok")
    rval, frame = vc.read()
    if c % timeF == 0:
        print(2)
        cv2.imwrite(outputFile + str(int(c / timeF)) + '.jpg', frame)
    c += 1
    cv2.waitKey(1)
vc.release()
