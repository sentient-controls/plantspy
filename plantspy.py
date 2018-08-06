#!/usr/bin/env python
import cv2
import StringIO
import numpy
import logging
import numpy as np
import imutils
from os import uname
from PIL import Image
from pylepton import Lepton
from traceback import format_exc
from influxdb import InfluxDBClient
from SocketServer import ThreadingMixIn
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer


LEP_WIDTH = 80
LEP_HEIGHT = 60

RESIZE_X = 800
RESIZE_Y = 600

#TODO: Move these to config file
INFLUX_IP    = '127.0.0.1'
INFLUX_PORT  = 8086
INFLUX_USER  = 'user'
INFLUX_PASS  = 'password'
INFLUX_DB    = 'database'

hostname = uname()[1]

LOGGER = logging.getLogger('')
LOGGER.setLevel(logging.DEBUG)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ This class allows to handle requests in separated threads.
        No further content needed, don't touch this. """


class ShapeDetector:
    def __init__(self):
        pass

    def detect(self, c):
        # initialize the shape name and approximate the contour
        shape = "unidentified"
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)

        # if the shape is a triangle, it will have 3 vertices
        if len(approx) == 3:
            shape = "triangle"

        # if the shape has 4 vertices, it is either a square or
        # a rectangle
        elif len(approx) == 4:
            # compute the bounding box of the contour and use the
            # bounding box to compute the aspect ratio
            (x, y, w, h) = cv2.boundingRect(approx)
            ar = w / float(h)

            # a square will have an aspect ratio that is approximately
            # equal to one, otherwise, the shape is a rectangle
            shape = "square" if ar >= 0.95 and ar <= 1.05 else "rectangle"

        # if the shape is a pentagon, it will have 5 vertices
        elif len(approx) == 5:
            shape = "pentagon"

        # otherwise, we assume the shape is a circle
        else:
            shape = "circle"

        # return the name of the shape
        return shape


class IRCamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        hud_color = (0,255,0)
        self.send_response(200)
        self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
        self.end_headers()
        while True:
            try:
                try:
                    (data, image, minVal, maxVal, minLoc, maxLoc) = capture()
                except Exception as e:
                    print(e)
                    print(format_exc())
                    continue
                #image = detect_leaf()
                # Apply the color map (heatmap)
                rgb_img = cv2.applyColorMap(image, cv2.COLORMAP_HOT)

                # Convert to RGB
                rgb_img = cv2.cvtColor(rgb_img, cv2.COLOR_BGR2RGB)

                # Display temperature to image
                display_temperature(rgb_img, maxVal, maxLoc, hud_color)

                # Display avg temperature
                display_avg_temp(data, rgb_img, (0, 255, 0))

                # Build MJPG image
                jpg = Image.fromarray(rgb_img)
                tmpFile = StringIO.StringIO()
                jpg.save(tmpFile, 'JPEG')
                self.wfile.write("--jpgboundary")
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(tmpFile.len))
                self.end_headers()
                jpg.save(self.wfile, 'JPEG')
                print("GOT HERE 1")

            except Exception as e:
                print(e)
                print(format_exc())
                break


def capture(flip_v=False, device="/dev/spidev0.1"):
    with Lepton(device) as l:
        data, _ = l.capture()

    minVal, maxVal, _, _ = cv2.minMaxLoc(data)
    resized_data = cv2.resize(data[:,:], (720, 480))
    _, _, minLoc, maxLoc = cv2.minMaxLoc(resized_data)

    # Detect leaf
    # resized_data     = detect_leaf(data)

    image = raw_to_8bit(resized_data)

    return (data, image, minVal, maxVal, minLoc, maxLoc)

def detect_leaf(image):
    # load the image and resize it to a smaller factor so that
    # the shapes can be approximated better
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)[1]
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    #sd = ShapeDetector()
    # loop over the contours
    for c in cnts:
        cv2.drawContours(image, [c], -1, (0, 255, 0), 1)
    cv2.imwrite('/tmp/ir_contour.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    return image

def store_value(conn, name, value):
    json_input = [{
        "measurement": name,
        "tags": {
            "sensor": name
        },
        "fields": {
            "value": value
        }
    }]
    conn.write_points(json_input)


def write_influx(pos_x, pos_y, temp):

    conn = InfluxDBClient(INFLUX_IP,
                          INFLUX_PORT,
                          INFLUX_USER,
                          INFLUX_PASS,
                          INFLUX_DB)
    store_value(conn,
                "sentient.{0}.temperature_f.01.max_pos_x".format(hostname),
                pos_x)
    store_value(conn,
                "sentient.{0}.temperature_f.01.max_pos_y".format(hostname),
                pos_y)
    store_value(conn,"sentient.{0}.temperature_f.01".format(hostname),
                temp)


def display_temperature(img, val_k, loc, color):
    val_f = ktof(val_k)
    val_c = ktoc(val_k)
    x, y = loc
    cv2.putText(img,"{0:.2f}F ({1:.2f}C)".format(val_f, val_c), (50,50),
                cv2.FONT_HERSHEY_PLAIN, 1.5, color, 4)
    cv2.line(img, (x - 40, y), (x + 40, y), color, 2)
    cv2.line(img, (x, y - 40), (x, y + 40), color, 2)
    # write_influx(x, y, val_f)

def display_avg_temp(data, img, color):
    mean = 0
    total_col = []
    for i in range(0, len(data)):
        total_col.append(numpy.mean(data[i]))
    mean = numpy.mean(total_col)
    temp_c = ktoc(mean)
    temp_f = ktof(mean)
    cv2.putText(img,
                "Avg: {0:.2f}F ({1:.2f}C)".format(temp_f, temp_c),
                (50,100),
                cv2.FONT_HERSHEY_PLAIN, 1.5, color, 4)


def raw_to_8bit(data):
    cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
    np.right_shift(data, 8, data)
    return cv2.cvtColor(np.uint8(data), cv2.COLOR_GRAY2RGB)

def ktof(val):
    return ((val / 100) * 1.8) - 459.67

def ktoc(val):
    return  (val / 100.00) - 273.15


def setup_logging():
    logFormatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    rootLogger.setLevel(logging.DEBUG)
# MAIN
def main():
    setup_logging()
    # Built HTTPServer and start
    server = ThreadedHTTPServer(('0.0.0.0', 80), IRCamHandler)

    try:
        print("Plantspy has been started for {0}".format(hostname))
        server.serve_forever()
    except KeyboardInterrupt:
        print("Ctrl-C was pressed exiting . . .")
    finally:
        server.socket.close()


if __name__ == '__main__':
    exit(main())
