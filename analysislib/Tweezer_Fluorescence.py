from lyse import *
from pylab import *
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
import tifffile as tiff
import matplotlib.patches as patches
import json
import csv
import os

data = data()
plotting=1

path=data['filepath']
print(path[0])

with Run(path[0]).open('r+') as shot:
        j=0
        img={}
        for i in ['Tweezer']:

            # Obtaining multiple images and averaging them:
            shot_image=shot.get_image('Andor_Camera',str(i),'tiff')
            if int(data['n_loop'].iloc[0])>1:
                img[str(i)] = np.average(shot_image.astype(np.float32),axis=0)
            else:
                img[str(i)]=shot_image.astype(np.float32)

            if False:#ROI Selection
                P0=(250,250)   # Starting point for the atoms ROI
                RX=250
                RY=250

                DX=(P0[0], P0[0]+RX)
                DY=(P0[1], P0[1]+RY)

                MOT=patches.Rectangle(P0, RX, RY, linewidth=1, edgecolor='r', facecolor='none') 

                p0=(150,100)   # Starting point for the correction area 
                rX=300
                rY=100

                dX=(p0[0], p0[0]+rX)
                dY=(p0[1], p0[1]+rY)

                corr=patches.Rectangle(p0, rX, rY, linewidth=1, edgecolor='b', facecolor='none')

                b0=(320,310)    # Starting point for the Probe area
                ray=270
                BEAM=patches.Circle(b0, ray, linewidth=1, edgecolor='y', facecolor='none')       
            if plotting:
                plt.figure(j+1)
                # plt.gca().add_patch(TweezRegion)
                plt.title(str(i))
                plt.imshow(img[str(i)])
                plt.show()       
            j+=1


             
