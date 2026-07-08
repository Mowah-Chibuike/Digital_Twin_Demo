import sys
import json
import sqlite3
import random
import cv2
import numpy as np
import paho.mqtt.client as mqtt

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QSlider, QLabel,
                             QPushButton, QAction, QDialog, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QDateTime
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *

MQTT_SERVER = "broker.hivemq.com"
ANGLE_TOPIC = "my_angles"

class MQTTTelemetryWorker(QThread):
    """Listens to the MQTT broker in the background and streams parsed data to the UI."""
    data_received = pyqtSignal(float, float, float) 

    def __init__(self):
        super().__init__()
        client_id = f"PyQtClient-{random.randint(0, 0xffff):04x}"
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def run(self):
        try:
            print(f"Connecting background network loop to {MQTT_SERVER}...")
            self.client.connect(MQTT_SERVER, 1883, keepalive=60)
        
            self.client.loop_forever()
        except Exception as e:
            print(f"MQTT Loop Error: {e}")

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print("Successfully subscribed to live telemetry pipeline stream!")
            self.client.subscribe(ANGLE_TOPIC)
        else:
            print(f"Broker connection rejected. Code: {reason_code}")

    def on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode('utf-8')
            data = json.loads(payload_str)
            
            if "x" in data and "y" in data and "z" in data:
                x_angle = float(data["x"])
                y_angle = float(data["y"])
                z_angle = float(data["z"])
                
                self.data_received.emit(x_angle, y_angle, z_angle)
        except Exception as e:
        
            pass

    def stop(self):
        self.client.disconnect()
        self.quit()
        self.wait()


class VideoExportWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, filename, fps, width, height):
        super().__init__()
        self.filename = filename ; self.fps = fps
        self.width = width       ; self.height = height
        self.writer = None

    def run(self):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.filename, fourcc, self.fps, (self.width, self.height))
        self.exec_()
        if self.writer:
            self.writer.release()
        self.finished.emit(self.filename)

    @pyqtSlot(QImage)
    def process_frame(self, q_img):
        q_img = q_img.convertToFormat(QImage.Format_RGB888)
        ptr = q_img.constBits()
        ptr.setsize(self.height * self.width * 3)
        frame = np.frombuffer(ptr, np.uint8).reshape((self.height, self.width, 3))
        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        if self.writer:
            self.writer.write(bgr_frame)

class VideoExportWorker(QThread):
    """Handles the heavy lifting of converting QImages and saving them to MP4 via OpenCV."""
    finished = pyqtSignal(str)

    def __init__(self, filename, fps, width, height):
        super().__init__()
        self.filename = filename
        self.fps = fps
        self.width = width
        self.height = height
        self.writer = None

    def run(self):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.filename, fourcc, self.fps, (self.width, self.height))
        
        self.exec_()
        
        if self.writer:
            self.writer.release()
        self.finished.emit(self.filename)

    @pyqtSlot(QImage)
    def process_frame(self, q_img):
        """Triggered asynchronously whenever a new frame is captured offscreen."""
       
        q_img = q_img.convertToFormat(QImage.Format_RGB888)
        ptr = q_img.constBits()
        ptr.setsize(self.height * self.width * 3)
        
        frame = np.frombuffer(ptr, np.uint8).reshape((self.height, self.width, 3))
        
        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        if self.writer:
            self.writer.write(bgr_frame)


class IMUVisualizerWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pitch = 0.0 ; self.yaw = 0.0 ; self.roll = 0.0  

    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.15, 1.0) 
        glEnable(GL_DEPTH_TEST)           
        glEnable(GL_CULL_FACE)            

    def resizeGL(self, width, height):
        if height == 0: height = 1
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / float(height), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
        self.draw_axes()
        glRotatef(self.yaw,   0.0, 0.0, 1.0)  
        glRotatef(self.pitch, 0.0, 1.0, 0.0)  
        glRotatef(self.roll,  1.0, 0.0, 0.0)  
        self.draw_box()

    def draw_axes(self):
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glColor3f(1.0, 0.2, 0.2) ; glVertex3f(0.0, 0.0, 0.0) ; glVertex3f(3.0, 0.0, 0.0)
        glColor3f(0.2, 1.0, 0.2) ; glVertex3f(0.0, 0.0, 0.0) ; glVertex3f(0.0, 3.0, 0.0)
        glColor3f(0.2, 0.5, 1.0) ; glVertex3f(0.0, 0.0, 0.0) ; glVertex3f(0.0, 0.0, 3.0)
        glEnd()
        glLineWidth(1.0)

    def draw_box(self):
        glBegin(GL_QUADS)
        glColor3f(0.8, 0.2, 0.2) ; glVertex3f(-1.0, -0.5, 1.5) ; glVertex3f(1.0, -0.5, 1.5) ; glVertex3f(1.0, 0.5, 1.5) ; glVertex3f(-1.0, 0.5, 1.5)
        glColor3f(0.2, 0.8, 0.2) ; glVertex3f(-1.0, -0.5, -1.5) ; glVertex3f(-1.0, 0.5, -1.5) ; glVertex3f(1.0, 0.5, -1.5) ; glVertex3f(1.0, -0.5, -1.5)
        glColor3f(0.2, 0.2, 0.8) ; glVertex3f(-1.0, 0.5, -1.5) ; glVertex3f(-1.0, 0.5, 1.5) ; glVertex3f(1.0, 0.5, 1.5) ; glVertex3f(1.0, 0.5, -1.5)
        glColor3f(0.8, 0.8, 0.2) ; glVertex3f(-1.0, -0.5, -1.5) ; glVertex3f(1.0, -0.5, -1.5) ; glVertex3f(1.0, -0.5, 1.5) ; glVertex3f(-1.0, -0.5, 1.5)
        glColor3f(0.2, 0.8, 0.8) ; glVertex3f(1.0, -0.5, -1.5) ; glVertex3f(1.0, 0.5, -1.5) ; glVertex3f(1.0, 0.5, 1.5) ; glVertex3f(1.0, -0.5, 1.5)
        glColor3f(0.8, 0.2, 0.8) ; glVertex3f(-1.0, -0.5, -1.5) ; glVertex3f(-1.0, -0.5, 1.5) ; glVertex3f(-1.0, 0.5, 1.5) ; glVertex3f(-1.0, 0.5, -1.5)
        glEnd()

    def update_orientation(self, pitch, roll, yaw):
        self.pitch = pitch ; self.roll = roll ; self.yaw = yaw
        self.update()


class RecordingsListWindow(QDialog):
    def __init__(self, db_filename, main_window_instance, parent=None):
        super().__init__(parent)
        self.db_filename = db_filename
        self.main_window = main_window_instance
        
        self.setWindowTitle("Saved IMU Recordings")
        self.resize(650, 450)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Session ID", "Recording Start Time", "Total Samples"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.export_btn = QPushButton("🎬 Export Selected Session to Video (Background)")
        
        self.export_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 13px;
                padding: 8px;
                background-color: #2b5b84;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3572a5;
            }
            QPushButton:disabled {
                background-color: #d3d3d3;
                color: #808080;
            }
        """)
        
        self.export_btn.clicked.connect(self.trigger_video_export)
        
        layout.addWidget(self.export_btn)
        
        self.load_recordings_from_db()

    def load_recordings_from_db(self):
        """Queries SQLite database to group data entries by unique recording sessions."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, MIN(timestamp), COUNT(*) 
                FROM imu_logs 
                GROUP BY session_id 
                ORDER BY MIN(timestamp) DESC
            """)
            records = cursor.fetchall()
            
            self.table.setRowCount(len(records))
            for row_idx, data in enumerate(records):
                session_id, start_time, sample_count = data
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(session_id)))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(start_time)))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(sample_count)))
            conn.close()
        except Exception as e:
            print(f"Error reading records from database: {e}")

    def trigger_video_export(self):
        """Identifies what row is highlighted and kicks off processing."""
        current_row = self.table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please click on a recording session from the list first!")
            return
            
        selected_session_id = self.table.item(current_row, 0).text()
        
        self.main_window.export_session_to_video(selected_session_id)
        
        self.accept()



class MainWindow(QMainWindow):
    sig_send_frame = pyqtSignal(QImage)
    sig_stop_worker = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live MQTT IMU Visualizer & Logger")
        self.resize(1000, 650)

        self.db_filename = "imu_data.db"
        self.db_conn = None ; self.db_cursor = None
        self.current_session_id = None
        self.is_recording = False
        self.init_sqlite_database()

        self.setup_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        self.gl_widget = IMUVisualizerWidget()
        main_layout.addWidget(self.gl_widget, stretch=3)

        control_layout = QVBoxLayout()
        main_layout.addLayout(control_layout, stretch=1)

        self.status_label = QLabel("Status: Connecting to Live Stream...")
        self.status_label.setStyleSheet("font-weight: bold; color: orange;")
        control_layout.addWidget(self.status_label)
        control_layout.addSpacing(10)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Record")
        self.pause_btn = QPushButton("Pause")
        self.stop_btn = QPushButton("Stop")
        
        self.start_btn.clicked.connect(self.start_recording)
        self.pause_btn.clicked.connect(self.pause_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.stop_btn)
        control_layout.addLayout(btn_layout)
        
        control_layout.addSpacing(20)
        control_layout.addWidget(QLabel("<b>Live Stream Matrix Feedback:</b>"))
        self.x_lbl = QLabel("Roll (X): 0.00°")  ; control_layout.addWidget(self.x_lbl)
        self.y_lbl = QLabel("Pitch (Y): 0.00°") ; control_layout.addWidget(self.y_lbl)
        self.z_lbl = QLabel("Yaw (Z): 0.00°")   ; control_layout.addWidget(self.z_lbl)

        control_layout.addStretch()
        self.update_button_states()

        self.mqtt_worker = MQTTTelemetryWorker()
        self.mqtt_worker.data_received.connect(self.handle_live_telemetry)
        self.mqtt_worker.start()

    def init_sqlite_database(self):
        try:
            self.db_conn = sqlite3.connect(self.db_filename)
            self.db_cursor = self.db_conn.cursor()
            self.db_cursor.execute("""
                CREATE TABLE IF NOT EXISTS imu_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TEXT,
                    roll REAL,
                    pitch REAL,
                    yaw REAL
                );
            """)
            self.db_conn.commit()
        except Exception as e:
            print(f"Database setup failure: {e}")

    def setup_menu_bar(self):
        menu_bar = self.menuBar()
        playback_menu = menu_bar.addMenu("Playback")
        view_action = QAction("View All Recordings", self)
        view_action.triggered.connect(self.open_recordings_window)
        playback_menu.addAction(view_action)

    def open_recordings_window(self):
        dialog = RecordingsListWindow(self.db_filename, self, self)
        dialog.exec_()


    @pyqtSlot(float, float, float)
    def handle_live_telemetry(self, x, y, z):
        """Executes safely on the main GUI thread every time an MQTT message is digested."""
        self.gl_widget.update_orientation(pitch=y, roll=x, yaw=z)
        
        self.x_lbl.setText(f"Roll (X): {x:.2f}°")
        self.y_lbl.setText(f"Pitch (Y): {y:.2f}°")
        self.z_lbl.setText(f"Yaw (Z): {z:.2f}°")
        
        if self.is_recording and self.current_session_id and self.db_cursor:
            current_time = QDateTime.currentDateTime().toString(Qt.ISODateWithMs)
            query = "INSERT INTO imu_logs (session_id, timestamp, roll, pitch, yaw) VALUES (?, ?, ?, ?, ?);"
            self.db_cursor.execute(query, (self.current_session_id, current_time, x, y, z))
            
            self.status_label.setText(f"Status: Streaming & Logging ({self.current_session_id})...")


    def start_recording(self):
        if not self.current_session_id:
            self.current_session_id = "RUN_" + QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
        self.is_recording = True
        self.status_label.setText("Status: Recording Stream...")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        self.update_button_states()

    def pause_recording(self):
        self.is_recording = False
        self.status_label.setText("Status: Recording Paused")
        self.status_label.setStyleSheet("font-weight: bold; color: orange;")
        self.update_button_states()

    def stop_recording(self):
        self.is_recording = False
        self.status_label.setText("Status: Saved to local Session Database")
        self.status_label.setStyleSheet("font-weight: bold; color: blue;")
        if self.db_conn:
            self.db_conn.commit()
        self.current_session_id = None
        self.update_button_states()

    def update_button_states(self):
        if self.is_recording:
            self.start_btn.setEnabled(False) ; self.pause_btn.setEnabled(True)  ; self.stop_btn.setEnabled(True)
        elif self.current_session_id is not None:
            self.start_btn.setEnabled(True)  ; self.pause_btn.setEnabled(False) ; self.stop_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(True)  ; self.pause_btn.setEnabled(False) ; self.stop_btn.setEnabled(False)

    def export_session_to_video(self, session_id):
        if not self.db_cursor: return
        try:
            self.db_cursor.execute("SELECT roll, pitch, yaw FROM imu_logs WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
            self.export_records = self.db_cursor.fetchall()
        except Exception as e:
            print(f"DB Read failure: {e}") ; return

        if not self.export_records: return

        self.export_width, self.export_height = 640, 480
        self.hidden_gl = IMUVisualizerWidget()
        self.hidden_gl.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.hidden_gl.setGeometry(-2000, -2000, self.export_width, self.export_height)
        self.hidden_gl.show()

        output_file = f"video_{session_id}.mp4"
        self.export_worker = VideoExportWorker(output_file, 20.0, self.export_width, self.export_height)
        self.sig_send_frame.connect(self.export_worker.process_frame)
        self.sig_stop_worker.connect(self.export_worker.quit)
        self.export_worker.finished.connect(self.on_export_complete)
        self.export_worker.start()

        self.export_index = 0
        self.pump_timer = QTimer(self)
        self.pump_timer.timeout.connect(self.process_next_background_frame)
        self.pump_timer.start(0)

    def process_next_background_frame(self):
        if self.export_index >= len(self.export_records):
            self.pump_timer.stop()
            self.sig_stop_worker.emit()
            return
        r, p, y = self.export_records[self.export_index]
        self.hidden_gl.pitch = p ; self.hidden_gl.roll = r ; self.hidden_gl.yaw = y
        self.hidden_gl.repaint()
        self.sig_send_frame.emit(self.hidden_gl.grabFramebuffer())
        self.export_index += 1

    def on_export_complete(self, filename):
        if self.hidden_gl:
            self.hidden_gl.close() ; self.hidden_gl = None
        self.status_label.setText("Status: Background video export finished!")
        self.status_label.setStyleSheet("font-weight: bold; color: blue;")

    def closeEvent(self, event):
        self.mqtt_worker.stop()
        if self.db_cursor: self.db_cursor.close()
        if self.db_conn:
            self.db_conn.commit()
            self.db_conn.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())