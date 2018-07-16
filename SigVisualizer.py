import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import random
from math import *
import time
import numpy as np
from pylsl import StreamInlet, resolve_stream

class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'PySigVisualizer'
        self.left = 10
        self.top = 20
        self.width = 1800
        self.height = 1000
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Set window background color
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)

        # Add paint widget and paint
        self.m = PaintWidget(self)
        self.m.move(0,0)
        self.m.resize(self.width,self.height)

        self.show()


class PaintWidget(QWidget):
    xMargin = 100
    yMargin = 50
    idx = -1
    chunkSize = 100

    # first resolve an EEG stream on the lab network
    print("looking for an EEG stream...")
    streams = resolve_stream('name', 'ActiChamp-0')
    # streams = resolve_stream('name', 'BioSemi')

    # create a new inlet to read from the stream
    inlet = StreamInlet(streams[0])
    samplingRate = int(streams[0].nominal_srate())
    channelCount = int(streams[0].channel_count())
    samplesPerScreen = 500
    timeStampsBuffer = np.zeros(shape=(channelCount, samplesPerScreen))
    dataBuffer = np.zeros(shape=(channelCount, samplesPerScreen))
    yScaling = 0.4
    xScaling = 1600 // samplesPerScreen
    trend = [0 for x in range(channelCount)]

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setPen(Qt.blue)
        channelHeight = (self.size().height() - 2 * self.yMargin) / self.channelCount
        self.yOffset = self.size().height() / self.channelCount / 2
        self.signalPanelWidth = self.size().width() - 2 * self.xMargin
        self.signalPanelHeight = self.size().height()

        # get a new sample (you can also omit the timestamp part if you're not
        # interested in it)
        chunk, timestamps = self.inlet.pull_chunk(max_samples=self.chunkSize)
        if timestamps:

            effectiveFS = (timestamps[-1] - timestamps[0]) / (len(timestamps) - 1)
            qp.drawText(100, self.channelCount * channelHeight + self.yOffset + self.yMargin, 
            'Effective sampling rate: {0:.2f}Hz'.format(round(1 / effectiveFS)))

            for c in range(len(timestamps)):
                self.idx = (self.idx + 1) % self.samplesPerScreen
                
                for m in range(self.channelCount):
                    self.dataBuffer[m, self.idx] = chunk[c][m] * self.yScaling

            if self.idx == self.chunkSize - 1:
                for m in range(self.channelCount):
                    self.trend[m] = np.mean(self.dataBuffer[m, 0:self.chunkSize])

        for m in range(self.channelCount):
            qp.drawText(10, m * channelHeight + self.yOffset + self.yMargin, 'Channel {}'.format(m+1))

            for k in range(self.dataBuffer.shape[1]-1):
                qp.drawLine(k * self.xScaling + self.xMargin, 
                self.dataBuffer[m, k] - self.trend[m] + m * channelHeight + self.yOffset / 2 + self.yMargin, 
                (k+1)*self.xScaling + self.xMargin, 
                self.dataBuffer[m, k+1] - self.trend[m] + m * channelHeight + self.yOffset / 2 + self.yMargin)

        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
