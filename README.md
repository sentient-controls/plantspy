# plantspy
Lepton 2.5 Radiometric Sensor with OpenCV HUD Temperature Hot Spot Detection 
and Avererage Frame Temperature

## Objective
Plantspy is a Python application that interfaces with the FLiR Lepton 2.5 Radiometric
long-wave infrared sensor connected to the SPI port of a Raspberry Pi 3. 
This sensor uses OpenCV to indicate the warmest point in
the frame while also creating an information layer on the images in real-time 
creating a heads up display (HUD) which indicates the average
frame temperature as well as the warmest location in the frame.

### Ok why?
In modern indoor commercial farming, knowing the average temperature (and standard 
deviation) of a leaf allows us to know the real-time temperature of a individual leaf 
by calculating vapor pressure over time. We can use this data
to make smart decisions for controlling the environment the plant lives in and 
in return allow for optimal fruiting [1].


## Updates
###2018-08-11
Imaging recognition is not quite complete, however we have started adding in
functions to start detecting leaves based on example input images that will
allow us to compare and match to. Updates forthcoming on this enhancement.

## Requirements and Installation 
For sake of not duplicating instructions that are freely available on-line 
we will link to outside resources below for wiring of the 
Lepton sensor to a Raspberry Pi 3 and the setup of the required libraries and 
software.

Plantspy, however, has not tested on previous versions of the Raspberry Pi 1 and 2. 
One can assume the only difference between hardware versions will be a slower 
frame rate and overall performance degradation of the application from the slower 
clock speeds. 

Currently Plantspy is single threaded but may be become multithreaded in 
the future so we recommend not using a Raspberry Pi 1.

### Connecting the Lepton
To connect the Lepton sensor to the Raspberry Pi we used the break-out board 
from GroupGets

https://groupgets.com/manufacturers/getlab/products/flir-lepton-breakout-board-v1-4

The instructions on how to wire the board are available at:

https://learn.sparkfun.com/tutorials/flir-lepton-hookup-guide


### Compiling OpenCV
Since we are using an infrared sensor we decided to apply the OpenCV heat map 
function to show the difference in temperature. 

https://en.wikipedia.org/wiki/Color_mapping

Unfortunately the OpenCV build shipped with Raspbian 8 does not contain this 
functionality. To add color mapping we have to compile OpenCV 3.x using 
OpenCV's contrib modules. To compile OpenCV 3.x follow the instructions here:

https://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/

### Running Plantspy
Once OpenCV is installed and all prerequisite Python libraries one can easily 
start the application by running it as the root.

```
# ./plantspy.ph
```

There is also a init.d startup script (plantspy without .py) supplied that 
allows one to auto-start Plantspy on boot. First make sure to change the 
startup path of where the application is located by editing the file and 
changing the line:

```
SCRIPT=/opt/software/plantspy/plantspy.py
```

```
# cp plantspy /etc/init.d
# rc-update add plantspy
````


## Examples

Example output from http://127.0.0.1:80/

![alt text](https://github.com/sentient-controls/plantspy/raw/master/docs/example.png)

# Resources
1. Shamshiri, Redmond & W Jones, James & Thorp, Kelly & Ahmad, Desa & Che Man, Hasfalina & Taheri, Sima. (2018). Review of optimum temperature, humidity, and vapour pressure deficit for microclimate evaluation and control in greenhouse cultivation of tomato: A review. International Agrophysics. 32. 287-302. 10.1515/intag-2017-0005. 
