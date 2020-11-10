
import os
f = open('F:\Projects\yolov3\slyolov3\data\\target.txt', 'w')
paths = "F:\Projects\yolov3\slyolov3\data\\gt\\"
files = os.listdir(paths)
files.sort()
for file in files:
    path = paths + file
    f.write(path + '\n')
f.close()



