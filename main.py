import datetime
import os
import re
import sys
from pathlib import Path
from textwrap import dedent

import pyperclip
from PyQt5.QtCore import QRunnable, Qt, QThread, QThreadPool, pyqtSignal, pyqtSlot, QProcess
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                             QMainWindow, QMessageBox, QPushButton,
                             QVBoxLayout, QWidget)
from pyqtspinner.spinner import WaitingSpinner

#----------GLOBALS ---------
version = 1.2

count_GLOBAL = 0
size_GLOBAL = 0
duration_GLOBAL = 0
frameRate_GLOBAL = []
resolution_GLOBAL = []

show_IMAGE_DETECTED_status_bar = False
errorFiles_GlOBAL = []
#---------------------------

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle('TD')
        self.setWindowOpacity(0.9) #-- Why? IDK, I think it's cool.

        self.bg_color = self.palette()
        self.bg_color.setColor(self.backgroundRole(), QColor(0,48,64))
        self.bg_color_drag = self.palette()
        self.bg_color_drag.setColor(self.backgroundRole(), QColor(4,14,18))
        self.setPalette(self.bg_color)

        self.statusBar_label = QLabel(' Image Detected')
        self.statusBar_label.setStyleSheet('color: #5dbcd2')
        self.statusBar().addWidget(self.statusBar_label)
        self.statusBar().hide()
        
        self.setAcceptDrops(True)

        widget = QWidget()

        #-----Objects in Layouts-------
        self.spinner = WaitingSpinner(
                self, True, True,
                roundness=70.0, opacity=15.0,
                fade=70.0, radius=14.0, lines=12,
                line_length=16.0, line_width=4.0,
                speed=1.5, color=(255, 255, 255)
            )

        self.top_label = QLabel()
        self.top_label.setFont(QFont("Arial", 14))
        self.top_label.setStyleSheet('color: white')
        self.top_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.top_label.setCursor(Qt.IBeamCursor)

        hLine = QFrame()
        hLine.setFrameShape(QFrame.HLine)
        hLine.setStyleSheet('color: white')

        self.bottom_label = QLabel()
        self.bottom_label.setFont(QFont("Arial", 14))
        self.bottom_label.setStyleSheet('color: white')
        self.bottom_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.bottom_label.setCursor(Qt.IBeamCursor)

        info_button_image_path = resource_path('./images/info_black.png')

        self.infoButton = QPushButton('', self)
        self.infoButton.setIcon(QIcon(info_button_image_path))
        self.infoButton.setCursor(Qt.PointingHandCursor)
        self.infoButton.clicked.connect(self.show_infoButton_message)
        self.infoButton.setMaximumWidth(30)
        self.infoButton.setToolTip("Info")
        self.infoButton.setFlat(True)
        
        #-------Layout Containers---------
        topHBox = QHBoxLayout()
        topHBox.addWidget(self.top_label)
        topHBox.addWidget(self.infoButton, 0, Qt.AlignRight | Qt.AlignTop)

        _layout = QVBoxLayout()
        _layout.addLayout(topHBox)
        _layout.addWidget(hLine, 0, Qt.AlignVCenter)
        _layout.addWidget(self.bottom_label)
        
        widget.setLayout(_layout)
        self.setCentralWidget(widget)

        self.start_here()

    ###########
    ## START ##
    ###########
    def start_here(self):
        '''
        Checks to see if triggered by drag-and-dropped files OR by Mac OS Service.

            -If run by service, list of files paths is appeneded to sys.argv
        '''

        if len(sys.argv) > 1:
            sys.argv.pop(0)
            self.consolodate_files(sys.argv)
        else:
            self.show_OR_update_MainWindow()

    def consolodate_files(self, fileList):
        '''
        Makes it recursive through folders
        '''

        file_path_list = []
        for x in fileList:                                      
            if x[0] != '.' and not os.path.isdir(x):    #1) Add all NON-hidden files to file_path_list (l)
                file_path_list.append(x)
            elif os.path.isdir(x):                      #2) If folder -> walk through and add all NON-hidden files to file_path_list
                for dirpath, subdirs, files in os.walk(x):
                    for y in files:
                        if not y.startswith('.'):
                            file_path_list.append(os.path.join(dirpath, y))

        self.start_ffprobe_thread(file_path_list)

    def start_ffprobe_thread(self, file_path_list):
        self.start_ffprobe_loop_thread = Start_ffprobe_Loop_Thread(file_path_list)
        self.start_ffprobe_loop_thread.threadPool_done.connect(lambda: self.show_OR_update_MainWindow())
        self.start_ffprobe_loop_thread.start()
        self.spinner.start()

    def show_OR_update_MainWindow (self):
        duration, size, frameRate, resolution = self.clean_up_label_numbers()
        self.update_labels(duration, size, frameRate, resolution)
        self.trigger_image_status_bar()
        self.spinner.stop()
        self.process_UI_events()
        self.test_if_error_message()

    def clean_up_label_numbers(self):
        try:
            duration = (str(datetime.timedelta(seconds=round(duration_GLOBAL))))
        except:
            duration = "Duration Invalid"
        size = self.format_bytes(size_GLOBAL)
        frameRate = ', '.join(self.remove_dupe(frameRate_GLOBAL))
        resolution = ', '.join(self.remove_dupe(resolution_GLOBAL))
        
        self.determine_wordwrap(resolution, frameRate)
        return duration, size, frameRate, resolution

    def update_labels(self, duration, size, frameRate, resolution):
        self.top_label.setText(dedent(f'''\
            Files:   {count_GLOBAL}

            Size:   {size}

            Duration:   {duration}''')
        )
        self.bottom_label.setText(dedent(f'''\
            Resolution(s):  {resolution}

            Frame Rate(s):  {frameRate}''')
        )
        self.determine_wordwrap(resolution, frameRate)

    def determine_wordwrap(self, resolution, frameRate):
        if len(resolution) > 100 or len(frameRate) > 100:
            self.bottom_label.setWordWrap(True)
        else:
            self.bottom_label.setWordWrap(False)

    def trigger_image_status_bar (self):       
        if show_IMAGE_DETECTED_status_bar == True:
            self.statusBar().show()
        else:
            self.statusBar().hide()
        
    def process_UI_events(self):
        QApplication.processEvents() #Helps with resizing of the window (if necessary)
        self.setFixedSize(self.sizeHint())
        self.show()

    def test_if_error_message(self):
        if len(errorFiles_GlOBAL) > 0:
            ErrorFiles_Message()

    def remove_dupe(self, a_list):
        final_list = list(dict.fromkeys(a_list))
        return final_list

    def format_bytes(self, size):
        power = 2**10
        n = 0
        power_labels = {0 : 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB', 5: 'PB', 6: 'EB'}
        while size > power:
            size /= power
            n += 1
        return f'{round(size, 2)} {power_labels[n]}'

    def show_infoButton_message(self):
        message = f'''
        <h3>Drag and Drop:</h3> 
        <p>Drag and drop media files onto app to caclulate total duration.</p>
        <h3><strong>Keyboard Shortcuts:</h3>
        <p style="text-indent: 15px;"><strong>c</strong> - Copy duration, close app</p>
        <p style="text-indent: 15px;"><strong>q</strong> - Close app</p>
        <br>
        <p>* This app is recursive; will dig through folders.<p>
        <br>
        v {version}
        '''
        Information_Message(message)

    def reset_vars (self):
        global count_GLOBAL, size_GLOBAL, duration_GLOBAL, frameRate_GLOBAL, errorFiles_GlOBAL, show_IMAGE_DETECTED_status_bar

        count_GLOBAL = 0
        size_GLOBAL = 0
        duration_GLOBAL = 0
        resolution_GLOBAL.clear()
        frameRate_GLOBAL.clear()
        errorFiles_GlOBAL.clear()
        show_IMAGE_DETECTED_status_bar = False

    #------DRAG AND DROP EVENT---------------------------------
    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].scheme() == 'file':
            self.setPalette(self.bg_color_drag)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.setPalette(self.bg_color)

    def dropEvent(self, event):
        data_obj = event.mimeData()
        urls = data_obj.urls()
        self.setPalette(self.bg_color)
        file_path_list = []
        if sys.platform == 'win32':
            for x in range(len(urls)):
                file_path_list.append(urls[x].path()[1:])
        else:
            for x in range(len(urls)):
                file_path_list.append(urls[x].path())
        self.reset_vars()
        self.consolodate_files(file_path_list)

    #------KEYPRESS EVENTS-------------------------------------   
    def keyPressEvent(self, event):
        super(MainWindow, self).keyPressEvent(event)
        if event.key() == Qt.Key_Q:
            self.q_keyPress()
        if event.key() == Qt.Key_C:
            self.c_keypress()

    def q_keyPress(self):
        sys.exit(0)

    def c_keypress(self):
        pyperclip.copy(str(datetime.timedelta(seconds=round(duration_GLOBAL))))
        sys.exit(0)


class Start_ffprobe_Loop_Thread(QThread):
    threadPool_done = pyqtSignal()

    def __init__(self, listOfFiles, *args, **kwargs):
        super(Start_ffprobe_Loop_Thread, self).__init__()
        self.listOfFiles = listOfFiles
        self.threadpool = QThreadPool()

    def run (self):
        for filePath in self.listOfFiles:
            self.kick_off_worker(filePath)
        self.threadpool.waitForDone()
        self.threadPool_done.emit()

    def kick_off_worker(self, filePath):
        worker = Worker(filePath)
        self.threadpool.start(worker)


class Worker(QRunnable):
    def __init__(self, filePath , *args, **kwargs):
        super(Worker, self).__init__()
        self.filePath = filePath

    @pyqtSlot()
    def run(self):
        self.test_file_type()

    def test_file_type(self):
        global errorFiles_GlOBAL, show_IMAGE_DETECTED_status_bar

        common_image_types = ['.jpg', '.png', '.tiff', '.tif']
        suffix = (Path(self.filePath).suffix.lower())
        if suffix == '.txt':
            errorFiles_GlOBAL.append(Path(self.filePath).name)
            return
        if suffix in common_image_types:  
            is_image_BOOL = True
            show_IMAGE_DETECTED_status_bar = True
        else:
            is_image_BOOL = False

        self.run_ffprobe(is_image_BOOL)

    def run_ffprobe(self, is_image_BOOL):
        program = str(Path('./ffprobe'))
        if is_image_BOOL == False:
            args = ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'format=duration,size:stream=width,height,r_frame_rate', self.filePath]
        else:
            args = ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'format=size:stream=width,height', self.filePath]
        
        process = QProcess()
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.start(program, args)
        if process.waitForFinished(-1):
            process.kill()
        ffprobe_output = bytearray(process.readAllStandardOutput()).decode('UTF-8')

        self.parse_ffprobe_out(ffprobe_output, is_image_BOOL)

    def parse_ffprobe_out (self, ffprobe_output, is_image_BOOL):
        '''
        Uses REGEX to parse standard output from ffprobe
        '''

        find_duration = re.compile(r'(duration=)(.*)')
        find_size = re.compile(r'(size=)(.*)')
        find_width = re.compile(r'(width=)(.*)')
        find_height = re.compile(r'(height=)(.*)')
        find_frameRate = re.compile(r'(r_frame_rate=)(.*)')

        try:
            size = find_size.findall(ffprobe_output)[0][1]

            width_test = find_width.findall(ffprobe_output)
            if len(width_test) > 0:
                width = width_test[0][1].rstrip() #rstrip is a MS Windows fix
                height = find_height.findall(ffprobe_output)[0][1]
                resolution = (f'{width}x{height}')
            else:
                resolution = ''
            
            if is_image_BOOL == False:
                duration = find_duration.findall(ffprobe_output)[0][1]
                frameRate_test = find_frameRate.findall(ffprobe_output)
                if len(frameRate_test) > 0:
                    frameRate = frameRate_test[0][1]
                else:
                    frameRate = ''
            else:
                duration = 0
                frameRate = ''
        except:
            errorFiles_GlOBAL.append(Path(self.filePath).name)
            return

        self.consolodate_ffprobe_out(duration, size, resolution, frameRate)  

    def consolodate_ffprobe_out(self, duration, size, resolution, frameRate):
        global count_GLOBAL, size_GLOBAL, duration_GLOBAL, frameRate_GLOBAL, resolution_GLOBAL, errorFiles_GlOBAL

        try:   
            duration_GLOBAL += (float(duration))
            count_GLOBAL += 1
            size_GLOBAL += (float(size))
            if resolution != '':
                resolution_GLOBAL.append(resolution)
            if frameRate != '':
                frameRate_GLOBAL.append(str(round(eval(frameRate),3)))
        except:
            errorFiles_GlOBAL.append(Path(self.filePath).name)


class Information_Message(QMessageBox):
    def __init__(self, message, *args, **kwargs):
        super().__init__()
        self.setIcon(QMessageBox.Information)
        self.setInformativeText(message)
        self.exec_()


class ErrorFiles_Message(QMessageBox):
    def __init__(self, *args, **kwargs):
        super().__init__()
        list_of_files = '\n'.join(errorFiles_GlOBAL)
        self.setIcon(QMessageBox.Warning)
        self.setText(f'Invalid or Corrupt Files\nTotal: {len(errorFiles_GlOBAL)}')

        if len(errorFiles_GlOBAL) < 15:
            self.setInformativeText(list_of_files)
        else:
            self.setInformativeText('Select "Show Details..." for list of files')
            self.setDetailedText(list_of_files)
        self.exec_()


def resource_path(relative_path):
    """ Translate asset paths to useable format for PyInstaller
    https://blog.aaronhktan.com/posts/2018/05/14/pyqt5-pyinstaller-executable """

    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path) 


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('images/GTD_icon.png'))) # MS Windows only
    window = MainWindow()
    sys.exit(app.exec_())