from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
import cv2, time

from os import system, name
import json
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget, QInputDialog, QAction
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, pyqtSlot,Qt
from PyQt5.QtWidgets import QMessageBox
from tools.UI_Main import *
import sys

class Main(QtWidgets.QMainWindow):
    # class constructor
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.uni = self.ui.unit_select.currentText() #"mm"#input("Desea hacer sus medidas en Milimetros[mm] o Pulgadas [in]")
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.quit = QAction("Quit", self)
        self.video=cv2.VideoCapture(0)
        self.display = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.get_measurements)
        self.timer.start(50)

        self.ui.toolButton.clicked.connect(self.close_app)
        self.ui.unit_select.currentTextChanged.connect(self.change_units)

        
    def close_app(self):
        try:
            self.timer.stop()
            
        except:
            pass
        self.close()

    def closeEvent(self, event):  # Close main window
        reply = QMessageBox.question(
            self, 'Close application', 'Are you sure you want to close the window?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Verificar que el dron esta en home y apagar todo
            self.video.release()
            print("Released")
            event.accept()
        else:
            self.timer.start(50)
            event.ignore()

    def change_units(self):
        self.uni = self.ui.unit_select.currentText()

    def midpoint(self, ptA, ptB):
        return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)
    

    def get_measurements(self):
        
        check, frame = self.video.read()
        # cv2.waitKey(0)
        # self.video.release()

        # cargar imagen, convertir a escala de grises y aplicarle filtro para reducir artefactos
        image = frame #cv2.imread(frame)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(gray, 50, 100)
        edged = cv2.dilate(edged, None, iterations=10)
        edged = cv2.erode(edged, None, iterations=10)
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0]# if imutils.is_cv2() else cnts[1]
        (cnts, _) = contours.sort_contours(cnts)
        pixelsPerMetric = None
        for c in cnts:
            if cv2.contourArea(c) < 100:
                continue
            orig = image.copy()
            box = cv2.minAreaRect(c)
            box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
            box = np.array(box, dtype="int")
            box = perspective.order_points(box)
            cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)
            for (x, y) in box:
                cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)
            (tl, tr, br, bl) = box
            (tltrX, tltrY) = self.midpoint(tl, tr)
            (blbrX, blbrY) = self.midpoint(bl, br)
            (tlblX, tlblY) = self.midpoint(tl, bl)
            (trbrX, trbrY) = self.midpoint(tr, br)
            cv2.circle(orig, (int(tltrX), int(tltrY)), 5, (255, 0, 0), -1)
            cv2.circle(orig, (int(blbrX), int(blbrY)), 5, (255, 0, 0), -1)
            cv2.circle(orig, (int(tlblX), int(tlblY)), 5, (255, 0, 0), -1)
            cv2.circle(orig, (int(trbrX), int(trbrY)), 5, (255, 0, 0), -1)
            cv2.line(orig, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)), (255, 0, 255), 2)
            cv2.line(orig, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)), (255, 0, 255), 2)
            dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
            dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
            
            if pixelsPerMetric is None:
                if self.uni == "mm":
                    pixelsPerMetric = dB / 24.257
                if self.uni == "in":
                    pixelsPerMetric = dB / .955
            dimA = dA / pixelsPerMetric
            dimB = dB / pixelsPerMetric
            if self.uni == 'mm':
                cv2.putText(orig, "{:.1f}mm".format(dimB), (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                cv2.putText(orig, "{:.1f}mm".format(dimA), (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            elif self.uni== "in":
                cv2.putText(orig, "{:.1f}in".format(dimB), (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                cv2.putText(orig, "{:.1f}in".format(dimA), (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            

            # self.display = orig
            self.display = cv2.resize(orig,(self.ui.video_display.width(),self.ui.video_display.height()),interpolation= cv2.INTER_LINEAR)
            height, width, channel = self.display.shape
            step = channel * width
            # create QImage from image
            qImg = QImage(self.display.data, width, height, step, QImage.Format_BGR888)
            # show image in img_label
            self.ui.video_display.setPixmap(QPixmap.fromImage(qImg))


def main_window():  # Run application
    app = QApplication(sys.argv)
    # create and show mainWindow
    mainWindow = Main()
    mainWindow.showMaximized()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main_window()