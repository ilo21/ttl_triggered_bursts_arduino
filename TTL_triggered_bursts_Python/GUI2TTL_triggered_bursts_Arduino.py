from gc import isenabled
import serial
import serial.tools.list_ports
from struct import pack
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import time
import warnings
warnings.filterwarnings("ignore")

DESIRED_FREQ_HZ = 25
HOW_MANY_SECONDS_PWM = 3
HIGH_PULSE_WIDTH_MS = 5

MIN_FREQ = 1
MAX_FREQ = 100
MIN_HIGH_PULSE_WIDTH = 1
MIN_DURATION = 1 
MAX_DURATION = 100

BAUDRATE = 115200
SENDING_TIMEOUT_NO = 50
RESET_CHAR = 'R'
QUIT_CHAR = 'Q'
COM = "COM5"

########################################
# SETTINGS CLASS
######################################
class MySettingsWidget(QMainWindow):
    
    def __init__(self):
        super(MySettingsWidget, self).__init__()
        self.name = "Settings"
        self.app_width = 300
        self.app_height = 30
        self.setWindowTitle(self.name)
        # self.setWindowIcon(QtGui.QIcon(ICO))
        self.resize(self.app_width,self.app_height)

        self.arduino = None
        
        self.task_params_dict = {
                                    "frequency":DESIRED_FREQ_HZ,
                                    "high_pulse_width":HIGH_PULSE_WIDTH_MS,
                                    "duration":HOW_MANY_SECONDS_PWM,
                                    "com":COM
                                }

        self.main_widget = QWidget()
        self.main_layout = QFormLayout()
        self.setCentralWidget(self.main_widget)       
        self.main_widget.setLayout(self.main_layout)
        self.frequency_label = QLabel("Frequency (Hz):")
        self.frequency_text = QLineEdit(str(self.task_params_dict["frequency"]))
        self.frequency_text.setValidator(QIntValidator())
        self.main_layout.addRow(self.frequency_label,self.frequency_text)
        self.pulse_width_label = QLabel("High pulse duration (ms)")
        self.pulse_width_text = QLineEdit(str(self.task_params_dict["high_pulse_width"]))
        self.pulse_width_text.setValidator(QIntValidator())
        self.main_layout.addRow(self.pulse_width_label,self.pulse_width_text)
        self.duration_label = QLabel("How long to send pulses (sec)")
        self.duration_text = QLineEdit(str(self.task_params_dict["duration"]))
        self.duration_text.setValidator(QIntValidator())
        self.main_layout.addRow(self.duration_label,self.duration_text)
        self.com_label = QLabel("COM port of the device")
        self.com_text = QLineEdit(str(self.task_params_dict["com"]))
        self.main_layout.addRow(self.com_label,self.com_text)

        self.start_btn_label = QLabel("")
        self.start_btn = QPushButton("Start")
        self.stop_btn_label = QLabel("")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.main_layout.addRow(self.start_btn_label,self.start_btn)
        self.main_layout.addRow(self.stop_btn_label,self.stop_btn)

        # make start button style
        self.startbutton_stylesheet = "QPushButton {font-size: 18px;font-weight: bold;color: green}"
        self.start_btn.setStyleSheet(self.startbutton_stylesheet)
        # make stop button style
        self.stopbutton_stylesheet = "QPushButton {font-size: 18px;font-weight: bold;color: red}"
        self.stop_btn.setStyleSheet(self.stopbutton_stylesheet)
        self.info_stylesheet = "QLabel {font-size: 18px;font-weight: bold;color: red}"
        self.stop_btn_label.setStyleSheet(self.info_stylesheet)

        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)

    def is_valid(self):
        valid = True
        pulse_width = int(self.pulse_width_text.text())
        freq = int(self.frequency_text.text())
        duration = int(self.duration_text.text())
        self.task_params_dict["com"] = self.com_text.text()
        if pulse_width < MIN_HIGH_PULSE_WIDTH or pulse_width > 99*10/freq:
            print(f"here{99*10/freq}")
            valid = False
        else:
            self.task_params_dict["high_pulse_width"] = pulse_width
        if freq < MIN_FREQ or freq > MAX_FREQ:
            valid = False
        else:
            self.task_params_dict["frequency"] = freq
        if duration < MIN_DURATION or duration > MAX_DURATION:
            valid = False
        else:
            self.task_params_dict["duration"] = duration
        return valid

    # define keypress events
    def keyPressEvent(self,event):
        # if enter is pressed start button clicked
        if event.key() == Qt.Key_Return:
            if self.start_btn.isEnabled():
                self.start()
            elif self.stop_btn.isEnabled():
                self.stop()

    def stop(self):
        try:
            self.stop_btn.setEnabled(False) # indicate early that button was clicked
            QApplication.processEvents()
            send_quit_ctr = 0
            print("Sending quit")
            # arduino doesn't always get the message, so try a few times and wait for confirmation
            while send_quit_ctr < SENDING_TIMEOUT_NO:
                time.sleep(1)
                send_quit_ctr +=1
                try:
                    self.arduino.write(bytes(QUIT_CHAR, 'utf-8','ignore'))
                except:
                    print("Could not send quit")
                time.sleep(0.5)
                line = self.arduino.readline()
                try:
                    data=line[0:][:-2].decode("utf-8")   
                    if data == QUIT_CHAR:
                        print(data)
                        break
                except:
                    print("Could not decode quit")
            self.arduino.close()
            print("Stopped")
            self.start_btn.setEnabled(True)
            self.stop_btn_label.setText("Stopped")
            QApplication.processEvents()
        except:
            print("Arduino already closed.\n\nExit")
        
    def start(self):
        valid = self.is_valid()
        if valid == False:
            error_msg = "Please make sure that:\nFrequency is between "+ str(MIN_FREQ)+" and "+str(MAX_FREQ)+"\nHigh pulse duration is between "+str(MIN_HIGH_PULSE_WIDTH)+" and "+str(99*10/int(self.frequency_text.text()))+"\nTime to send pulses is between "+str(MIN_DURATION)+" and "+str(MAX_DURATION)
            self.show_info_dialog(error_msg)
        else:
            print(self.task_params_dict)
            try:
                self.arduino = serial.Serial(self.task_params_dict["com"], baudrate= BAUDRATE, timeout = 2)
                self.start_btn.setEnabled(False)
                QApplication.processEvents()
                self.send_parameters()
                self.stop_btn.setEnabled(True)
                self.stop_btn_label.setText("Armed")
                QApplication.processEvents()
            except:
                self.show_info_dialog("Could not connect to the device.\nPlease double check your COM port")
    
    def send_parameters(self):
        message = str(self.task_params_dict["frequency"])+","+str(self.task_params_dict["high_pulse_width"])+","+str(self.task_params_dict["duration"])
        arg = bytes(message, 'utf-8','ignore') + b'\n'
        received = False
        sending_params_ctr = 0
        sending_confirmation_ctr = 0
        # arduino doesn't always get and assign the whole string message, so try a few times and wait for confirmation
        while sending_params_ctr < SENDING_TIMEOUT_NO and received == False:   
            time.sleep(1)
            sending_params_ctr+=1
            # send end of message
            self.arduino.flushInput()
            self.arduino.flushOutput()
            print(f"{sending_params_ctr}. Sending {message}")
            try:            
                self.arduino.write(arg)
                time.sleep(0.5)
                line = self.arduino.readline()           
                try:
                    data=line[0:][:-2].decode("utf-8") 
                    data_list = data.split(",")
                    print(f"Received {data}")
                    if len(data_list) == 3: # wait until arduino confirms that it has set all 3 values correctly
                        if data_list[0] == str(self.task_params_dict["frequency"]) and data_list[1] == str(self.task_params_dict["high_pulse_width"]) and data_list[2] == str(self.task_params_dict["duration"]):
                            try:    # if it set values properly, wait until it confimrs
                                while sending_confirmation_ctr < SENDING_TIMEOUT_NO:
                                    sending_confirmation_ctr+=1
                                    self.arduino.write(bytes(RESET_CHAR, 'utf-8','ignore')) # send Reset character to confirm to arduino
                                    time.sleep(0.3)
                                    line = self.arduino.readline()
                                    try:
                                        data=line[0:][:-2].decode("utf-8")   
                                        if data == RESET_CHAR:
                                            print(data)
                                            received = True  # mark as received and confirmed
                                            break
                                    except:
                                        print("Could not decode confirmation")
                            except:
                                print("Write confirmation timeout")
                except:
                    print("Could not decode received parameter data")
            except:
                print("Write parameters timeout")

    # show info that only ins are streamed
    def show_info_dialog(self, text):
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.setWindowTitle("Info!")
        # msgBox.setWindowIcon(QtGui.QIcon(ICO))
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.exec()

    def closeEvent(self, event): 
        self.stop()

################################################################
#                                                              #
# EXECUTE GUI FROM MAIN                                        #
#                                                              #
################################################################
if __name__ == "__main__":
    # Always start by initializing Qt (only once per application)
    app = QApplication([])
    main_widget = MySettingsWidget()
    main_widget.show()
    app.exec_()
   

    print('Done')