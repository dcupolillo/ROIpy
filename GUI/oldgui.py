""" Created on Sat Oct  7 11:52:17 2023
    @author: dcupolillo """

import os
import sys

import numpy as np
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, \
    QMessageBox, QFileDialog, QGridLayout, QLabel, QPushButton, \
    QProgressBar, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, \
    QLineEdit, QAction, QGraphicsPathItem, QCheckBox, QFrame, QComboBox, \
    QSlider, QGraphicsEllipseItem, QDesktopWidget
from PyQt5.QtGui import QKeySequence, QPainter, QPen, QPainterPath, \
    QPolygonF, QIntValidator, QDoubleValidator, QColor, QIcon
from PyQt5.QtCore import Qt, QPointF, pyqtSignal

import pyqtgraph as pg

from ROIpy.assets.palette import dim

from ROIpy.core.structures import Stack, Morphology, Scanfields





class GUI(QMainWindow):
    
    
    def __init__(self):
        
        super().__init__()
        
        self._work_dir = os.path.dirname(__file__) 
        self._window_geometry()
        self._init_stylesheets()
        self._icons()
        self._init_window()
        self._init_variables()
        self._init_frames()
        
               
    def _init_variables(self):
        
        # self.icon_name = None

        self._zs = [None] 
        
        self._swc_filename = None
        self._tif_filename = None
        
        self._is_image_plot = False
            
        self._framerate = None
        self._wavelenght = None
        self._dwelltime = None
        self._flyback = None
        self._pixbin = None
        self._samplerate = None
        self._fillfraction = None
        
        
    def _init_stylesheets(self):
        
        self._buttonsize = (60, 40)
        self._buttonradius = 2
        self._buttonfontsize = '10pt'
        
        self._entrysize = (250, 30)
        self._entryfontsize = '10pt'
        
        self._labelfontsize = '10pt'
        self._titlefontsize = '12pt'
        
        self._button_stylesheet = (
           f'''QPushButton {{ color: {dim.light};
                              background-color: {dim.d_dark};
                              width: {self._buttonsize[0]}; 
                              height: {self._buttonsize[1]}; 
                              border-radius : {self._buttonradius};
                              font-size: {self._buttonfontsize}; 
                             }}
               QPushButton:hover {{ background-color: {dim.hovering};
                                   }}''')
               
        self._entry_stylesheet = (
           f'''QLineEdit {{ border: none; 
                            background-color: {dim.d_dark};
                            color: {dim.light};
                            width: {self._entrysize[0]}; 
                            height: {self._entrysize[1]}; 
                            font-size: {self._entryfontsize}
                            }}''')
            
        self._choosefolder_stylesheet = (
            f'''QLabel {{ border: none; 
                          background-color: {dim.d_dark};
                          color: {dim.light};
                          width: {self._entrysize[0]}; 
                          height: {self._entrysize[1]}; 
                          font-size: {self._entryfontsize}
                          }}''')
        
        self._label_stylesheet = (
            f'''QLabel {{ color: {dim.light};
                          font-size: {self._labelfontsize};
                          }}''')
                
        self._title_stylesheet = (
            f'''color:{dim.blue}; 
                font-weight: bold; 
                font-size: {self._titlefontsize};''')
                
        self._slider_stylesheet = (
            f'''QSlider::groove:horizontal {{ background: {dim.d_dark}; }}
                QSlider::handle:horizontal {{ background: {dim.blue}; 
                                              width: 18px; 
                                              margin: -8px 0; }}''')
            
        
    def _window_geometry(self):
        
        self._central_widget = QWidget(self)
        self._grid_layout = QGridLayout(self._central_widget)
        self.setCentralWidget(self._central_widget)
              
        desktop = QDesktopWidget()
        screen = desktop.availableGeometry()
        self._screen_width = screen.width()
        self._screen_height = screen.height()
        
        self._window_height = 900
        self._window_width = 1700
        self._window_left_offset = (self._screen_width - self._window_width) //2
        self._window_top_offset = 50
        
    
    def _init_window(self):

        self.setStyleSheet(f'background-color:{dim.black}')
        self.setWindowTitle('ROIpy')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # self.setWindowIcon(QIcon(self.icon_name))
        self.setGeometry(self._window_left_offset, self._window_top_offset, 
                         self._window_width, self._window_height)
        
        
    def _init_frames(self):
        
        self._frame_load()
        self._frame_morph()
        self._canvas()
        self._canvas_control()
        self._frame_scanfield()
        self._frame_save()
        self._frame_exit()
        
        
    def _icons(self):
        
        # Load icons for displaying
        
        iconfolder_path = self._work_dir + '\\assets\\icons\\'
        self._folder_icon = iconfolder_path + 'folder.png'
        self._neuron_icon = iconfolder_path + 'nodes.png'
        self._rect_icon = iconfolder_path + 'rectangles.png'
        self._next_icon = iconfolder_path + 'next.png'
        self._layers_icon = iconfolder_path + 'layers.png'
        self._quit_icon = iconfolder_path + 'exit.png'
        self._load_icon = iconfolder_path + 'load.png'
        self._plot_icon = iconfolder_path + 'plot.png'
        self._reset_icon = iconfolder_path + 'reset.png'
        self._savefile_icon = iconfolder_path + 'savefile.png'
        self._image_icon = iconfolder_path + 'image.png'
        
    
    def _create_frame(self, col, row, col_span = 1, row_span = 1):
       
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShape(QFrame.NoFrame)
        frame.setStyleSheet(f'background-color:{dim.dark}')

        self._grid_layout.addWidget(frame, row, col, row_span, col_span)
        
        return frame
        
    
    def _frame_load(self):
        
        self._frame_load = self._create_frame(0, 0)
        frame_load_layout = QGridLayout(self._frame_load)
        
        title = QLabel("Load files\n")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(self._title_stylesheet)
        frame_load_layout.addWidget(title, 0, 0, 1, 3)
        
        # SWC load
        
        label_swc = QLabel('.swc file:')
        label_swc.setStyleSheet(self._label_stylesheet)
        label_swc.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        
        self._swc_label = QLabel()
        self._swc_label.setWordWrap(False)
        self._swc_label.setFixedWidth(self._entrysize[0])
        self._swc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._swc_label.setStyleSheet(self._choosefolder_stylesheet)
        
        self._swc_button = QPushButton(' Choose', self._central_widget)
        self._swc_button.setIcon(QIcon(self._folder_icon))
        self._swc_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering};}}''')
        self._swc_button.clicked.connect(lambda: self._choose_file('swc', self._swc_label))
        
        frame_load_layout.addWidget(label_swc, 1, 0)
        frame_load_layout.addWidget(self._swc_label, 1, 1)
        frame_load_layout.addWidget(self._swc_button, 1, 2)
        
        # TIF load
        
        label_tif = QLabel('.tif file:')
        label_tif.setStyleSheet(self._label_stylesheet)
        label_tif.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self._tif_label = QLabel()
        self._tif_label.setWordWrap(False)
        self._tif_label.setFixedWidth(self._entrysize[0])
        self._tif_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._tif_label.setStyleSheet(self._choosefolder_stylesheet)
        
        self._tif_button = QPushButton(' Choose', self._central_widget)
        self._tif_button.setIcon(QIcon(self._folder_icon))
        self._tif_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
        self._tif_button.clicked.connect(lambda: self._choose_file('tif', self._tif_label))
        
        frame_load_layout.addWidget(label_tif, 2, 0)
        frame_load_layout.addWidget(self._tif_label, 2, 1)
        frame_load_layout.addWidget(self._tif_button, 2, 2)
        

       

        self._generate_button = QPushButton(' Generate')
        self._generate_button.setIcon(QIcon(self._next_icon))
        self._generate_button.setStyleSheet(f'''QPushButton {{ color: {dim.light};
                                                    background-color: {dim.green};
                                                    width: {self._buttonsize[0]}; 
                                                    height: {self._buttonsize[1]}; 
                                                    border-radius : {self._buttonradius};
                                                    font-size: {self._buttonfontsize}; 
                                                    }}
                                      QPushButton:hover {{ background-color: {dim.hovering};
                                                             }}''')
                                      
        self._generate_button.setEnabled(False)
        self._generate_button.clicked.connect(lambda: self._generate(self._swc_label.text(), 
                                                                     self._tif_label.text()))
        
        frame_load_layout.addWidget(self._generate_button, 3, 2)
        
        
    def _frame_morph(self):
        
        self._frame_morph = self._create_frame(0, 1)
        frame_morph_layout = QGridLayout(self._frame_morph)
        
        title = QLabel("Morphology\n")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(self._title_stylesheet)
        frame_morph_layout.addWidget(title, 0, 0, 1, 3)

        # Whole Neuron
        
        label_neuron = QLabel('Neuron')
        label_neuron.setStyleSheet(self._label_stylesheet)
        label_neuron.setAlignment(Qt.AlignCenter)
        
        self._neuron_morph_button = QPushButton()
        self._neuron_morph_button.setIcon(QIcon(self._neuron_icon))
        self._neuron_morph_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
        self._neuron_morph_button.setEnabled(False)
                                            
        
        self._neuron_scanf_button = QPushButton()
        self._neuron_scanf_button.setIcon(QIcon(self._rect_icon))
        self._neuron_scanf_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
        self._neuron_scanf_button.setEnabled(False)
        
        # self._neuron_morph_button.clicked.connect(lambda: None)
        # self._neuron_scanf_button.clicked.connect(lambda: None)
        frame_morph_layout.addWidget(label_neuron, 1, 0)
        frame_morph_layout.addWidget(self._neuron_morph_button, 2, 0)
        frame_morph_layout.addWidget(self._neuron_scanf_button, 3, 0)
        
        # Apical dendrite
        
        label_apical = QLabel('Apical')
        label_apical.setStyleSheet(self._label_stylesheet)
        label_apical.setAlignment(Qt.AlignCenter)
        
        self._apical_morph_button = QPushButton()
        self._apical_morph_button.setIcon(QIcon(self._neuron_icon))
        self._apical_morph_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
        self._apical_morph_button.setEnabled(False)
                                                
        self._apical_scanf_button = QPushButton()
        self._apical_scanf_button.setIcon(QIcon(self._rect_icon))
        self._apical_scanf_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
        self._apical_scanf_button.setEnabled(False)
        
        # self._apical_morph_button.clicked.connect(lambda: None)
        # self._apical_scanf_button.clicked.connect(lambda: None)
        frame_morph_layout.addWidget(label_apical, 1, 1)
        frame_morph_layout.addWidget(self._apical_morph_button, 2, 1)
        frame_morph_layout.addWidget(self._apical_scanf_button, 3, 1)

        # Basal dendrite
        
        label_basal = QLabel('Basal')
        label_basal.setStyleSheet(self._label_stylesheet)
        label_basal.setAlignment(Qt.AlignCenter)
        
        self._basal_morph_button = QPushButton()
        self._basal_morph_button.setIcon(QIcon(self._neuron_icon))
        self._basal_morph_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
        self._basal_morph_button.setEnabled(False)
                                               
        self._basal_scanf_button = QPushButton()
        self._basal_scanf_button.setIcon(QIcon(self._rect_icon))
        self._basal_scanf_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
        self._basal_scanf_button.setEnabled(False)
                                          
        # self._basal_morph_button.clicked.connect(lambda: None)
        # self._basal_scanf_button.clicked.connect(lambda: None)
        frame_morph_layout.addWidget(label_basal, 1, 2)
        frame_morph_layout.addWidget(self._basal_morph_button, 2, 2)
        frame_morph_layout.addWidget(self._basal_scanf_button, 3, 2)

        
    def _canvas(self):
        
        self._imv = self._create_frame(1, 0, 1, 4)
        self._imv_layout = QGridLayout(self._imv)
        
        self._z_slider = QSlider(Qt.Horizontal)
        self._z_slider.setEnabled(False)
        self._z_slider.setStyleSheet(self._slider_stylesheet)

        self._channel_slider = QSlider(Qt.Horizontal)
        self._channel_slider.setEnabled(False)
        self._channel_slider.setStyleSheet(self._slider_stylesheet)

        # Connect slider signals to update the displayed image
        self._z_slider.valueChanged.connect(self._update_image)
        self._channel_slider.valueChanged.connect(self._update_image)
        
        self._imv = pg.ImageView()
        self._imv.setMinimumWidth(800)
        self._imv.setMinimumHeight(400)
        self._imv.getHistogramWidget().setFixedWidth(80)
        self._imv.ui.roiBtn.setVisible(False)
        self._imv.ui.menuBtn.setVisible(False)
        
        self._imv_layout.addWidget(self._imv, 0, 0)
        self._imv_layout.addWidget(self._z_slider, 1, 0, 1, -1)
        self._imv_layout.addWidget(self._channel_slider, 2, 0, 1, -1)
        
    
    def _canvas_control(self):
        
        self._canvas_control = self._create_frame(1, 5)
        canv_contr_layout = QGridLayout(self._canvas_control)
        
        self._image_button = QPushButton()
        self._image_button.setText(" Display stack")
        self._image_button.setIcon(QIcon(self._image_icon))
        self._image_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
        self._image_button.setEnabled(False)
        self._image_button.clicked.connect(lambda: self._plot_image())
                                                 
        self._clear_image_button = QPushButton()
        self._clear_image_button.setText(" Clear stack")
        self._clear_image_button.setIcon(QIcon(self._image_icon))
        self._clear_image_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')

        self._clear_image_button.setEnabled(False)
        self._clear_image_button.clicked.connect(lambda: self._clear_image())
            
                                               
        self._morph_button = QPushButton()
        self._morph_button.setText(" Display morphology")
        self._morph_button.setIcon(QIcon(self._neuron_icon))
        self._morph_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
                                                 
        self._clear_morph_button = QPushButton()
        self._clear_morph_button.setText(" Clear morohology")
        self._clear_morph_button.setIcon(QIcon(self._neuron_icon))
        self._clear_morph_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
                                               
        self._scanf_button = QPushButton()
        self._scanf_button.setText(" Display scanfield")
        self._scanf_button.setIcon(QIcon(self._rect_icon))
        self._scanf_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
                                                 
        self._clear_scanf_button = QPushButton()
        self._clear_scanf_button.setText(" Clear scanfield")
        self._clear_scanf_button.setIcon(QIcon(self._rect_icon))
        self._clear_scanf_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering}}}''')
                                                 
        canv_contr_layout.addWidget(self._image_button, 0, 0)
        canv_contr_layout.addWidget(self._clear_image_button, 1, 0)
        canv_contr_layout.addWidget(self._morph_button, 0, 1)
        canv_contr_layout.addWidget(self._clear_morph_button, 1, 1)
        canv_contr_layout.addWidget(self._scanf_button, 0, 2)
        canv_contr_layout.addWidget(self._clear_scanf_button, 1, 2)
        
    def _frame_scanfield(self):
        
        self._frame_scanfield = self._create_frame(0, 2)
        frame_scanfield_layout = QGridLayout(self._frame_scanfield)
        
        title = QLabel("Scan Properties\n")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(self._title_stylesheet)
        frame_scanfield_layout.addWidget(title, 0, 0, 1, 4)
        
        # Framerate
        self._label_framerate = QLabel('Desired Framerate [Hz] :')
        self._label_framerate.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._label_framerate.setStyleSheet(self._label_stylesheet)
        frame_scanfield_layout.addWidget(self._label_framerate, 1, 0)
        
        self._framerate = QLineEdit()
        self._framerate.setFixedWidth(self._entrysize[0])
        self._framerate.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._framerate.setStyleSheet(self._entry_stylesheet)
        frame_scanfield_layout.addWidget(self._framerate, 1, 1)
        
        # Wavelenght
        self._label_wavelenght = QLabel('Wavelenght [nm]:')
        self._label_wavelenght.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._label_wavelenght.setStyleSheet(self._label_stylesheet)
        frame_scanfield_layout.addWidget(self._label_wavelenght, 2, 0)
        
        self._wavelenght = QLineEdit()
        self._wavelenght.setFixedWidth(self._entrysize[0])
        self._wavelenght.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._wavelenght.setStyleSheet(self._entry_stylesheet)
        frame_scanfield_layout.addWidget(self._wavelenght, 2, 1)
        
        # Pixel Dwell time
        self._label_dwelltime = QLabel('Dwell time [s] :')
        self._label_dwelltime.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._label_dwelltime.setStyleSheet(self._label_stylesheet)
        frame_scanfield_layout.addWidget(self._label_dwelltime, 3, 0)
        
        self._dwelltime = QLineEdit()
        self._dwelltime.setFixedWidth(self._entrysize[0])
        self._dwelltime.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._dwelltime.setStyleSheet(self._entry_stylesheet)
        frame_scanfield_layout.addWidget(self._dwelltime, 3, 1)
        
        # Pixel Bin Factor
        self._label_pixbin = QLabel('Pixel Bin Factor :')
        self._label_pixbin.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._label_pixbin.setStyleSheet(self._label_stylesheet)
        frame_scanfield_layout.addWidget(self._label_pixbin, 4, 0)
        
        self._pixbin = QLineEdit()
        self._pixbin.setFixedWidth(self._entrysize[0])
        self._pixbin.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._pixbin.setStyleSheet(self._entry_stylesheet)
        frame_scanfield_layout.addWidget(self._pixbin, 4, 1)
        
        # Frame Flyback time
        self._label_flyback = QLabel('Flyback time [s] :')
        self._label_flyback.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._label_flyback.setStyleSheet(self._label_stylesheet)
        frame_scanfield_layout.addWidget(self._label_flyback, 1, 2)
        
        self._flyback = QLineEdit()
        self._flyback.setFixedWidth(self._entrysize[0])
        self._flyback.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._flyback.setStyleSheet(self._entry_stylesheet)
        frame_scanfield_layout.addWidget(self._flyback, 1, 3)
        
        # Fly to line time
        self._label_flytoline = QLabel('Flytoline time [s] :')
        self._label_flytoline.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._label_flytoline.setStyleSheet(self._label_stylesheet)
        frame_scanfield_layout.addWidget(self._label_flytoline, 2, 2)
        
        self._flytoline = QLineEdit()
        self._flytoline.setFixedWidth(self._entrysize[0])
        self._flytoline.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._flytoline.setStyleSheet(self._entry_stylesheet)
        frame_scanfield_layout.addWidget(self._flytoline, 2, 3)
        
        # Sampling Rate
        self._label_samprate = QLabel('Sampling Rate [Hz] :')
        self._label_samprate.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._label_samprate.setStyleSheet(self._label_stylesheet)
        frame_scanfield_layout.addWidget(self._label_samprate, 3, 2)
        
        self._samplerate = QLineEdit()
        self._samplerate.setFixedWidth(self._entrysize[0])
        self._samplerate.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._samplerate.setStyleSheet(self._entry_stylesheet)
        frame_scanfield_layout.addWidget(self._samplerate, 3, 3)
        
        # Fill Fraction
        self._labelfillfraction = QLabel('Fill Fraction :')
        self._labelfillfraction.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._labelfillfraction.setStyleSheet(self._label_stylesheet)
        frame_scanfield_layout.addWidget(self._labelfillfraction, 4, 2)
        
        self._fillfraction = QLineEdit()
        self._fillfraction.setFixedWidth(self._entrysize[0])
        self._fillfraction.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._fillfraction.setStyleSheet(self._entry_stylesheet)
        frame_scanfield_layout.addWidget(self._fillfraction, 4, 3)
        
    
    def _frame_save(self):
            
        self._frame_save = self._create_frame(0, 3)
        frame_save_layout = QGridLayout(self._frame_save)
        
        title = QLabel("Save ROIs\n")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(self._title_stylesheet)
        frame_save_layout.addWidget(title, 0, 0, 1, 3)
        
        label_save = QLabel('Save To:')
        label_save.setStyleSheet(self._label_stylesheet)
        label_save.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self._save_label = QLabel()
        self._save_label.setWordWrap(False)
        self._save_label.setFixedWidth(self._entrysize[0])
        self._save_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._save_label.setStyleSheet(self._choosefolder_stylesheet)
        
        self._savelocation_button = QPushButton(' Choose', self._central_widget)
        self._savelocation_button.setIcon(QIcon(self._folder_icon))
        self._savelocation_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering};}}''')
        self._savelocation_button.clicked.connect(lambda: None)
        
        self._save_button = QPushButton(' Save')
        self._save_button.setIcon(QIcon(self._next_icon))
        self._save_button.setStyleSheet(f'''QPushButton {{ color: {dim.light};
                                                    background-color: {dim.green};
                                                    width: {self._buttonsize[0]}; 
                                                    height: {self._buttonsize[1]}; 
                                                    border-radius : {self._buttonradius};
                                                    font-size: {self._buttonfontsize}; 
                                                    }}
                                      QPushButton:hover {{ background-color: {dim.hovering};
                                                          }}''')
        self._save_button.setEnabled(False)
        
        frame_save_layout.addWidget(label_save, 1, 0)
        frame_save_layout.addWidget(self._save_label, 1, 1)
        frame_save_layout.addWidget(self._savelocation_button, 1, 2)
        frame_save_layout.addWidget(self._save_button, 2, 2)
        
        
    def _frame_exit(self):
        
        spacer = spacer = QWidget()
        spacer.setMinimumSize(self._buttonsize[0], self._buttonsize[1])
        
        self._frame_exit = self._create_frame(0, 5)
        frame_exit_layout = QGridLayout(self._frame_exit)
        
        self._reset_button = QPushButton('Reset', self._central_widget)
        self._reset_button.setIcon(QIcon(self._reset_icon))
        self._reset_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering};}}''')
                                         
        self._exit_button = QPushButton('Quit', self._central_widget)
        self._exit_button.setIcon(QIcon(self._quit_icon))
        self._exit_button.setStyleSheet(self._button_stylesheet + 
                                       f'''QPushButton:hover {{ 
                                       background-color: {dim.hovering};}}''')
                                        
        self._exit_button.clicked.connect(self._on_closing)
                                         
        frame_exit_layout.addWidget(spacer, 0, 1)
        frame_exit_layout.addWidget(self._reset_button, 0, 2)
        frame_exit_layout.addWidget(self._exit_button, 0, 3)
        

    def _choose_file(self, file_format, label):
       
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        
        file_filter = f"{file_format} Files (*.{file_format})"
        
        file_name, _ = QFileDialog.getOpenFileName(self, 
                                                   f"Open .{file_format} File", 
                                                   "", 
                                                   file_filter, options=options)
        
        if file_name:
            label.setText(file_name) 
            label.setStyleSheet(self._choosefolder_stylesheet)
            
        if file_format == 'swc':
            self._swc_filename = file_name
        elif file_format == 'tif':
            self._tif_filename = file_name
            
        self._is_file_load()
        
    
    def _is_file_load(self, *args):

        # Check if input files are loaded and, in case, activate Generate button
  
        if self._swc_label.text() and self._tif_label.text():    
            self._generate_button.setEnabled(True)                                     
            
        else:
            self._generate_button.setEnabled(False)    
            
            
    def _generate(self, swc, tif):
        
        # Creates the module objects
        
        self._stack = Stack(tif)
        self._morph = Morphology(tif, swc)
        self._sf = Scanfields(tif, swc)
        self._zs = self._stack.zs
        self._filename = self._stack.stackName
        self._update_scanfield_parameters()
        
        self._neuron_morph_button.setEnabled(True)
        self._neuron_scanf_button.setEnabled(True)
        self._apical_morph_button.setEnabled(True)
        self._apical_scanf_button.setEnabled(True)
        self._basal_morph_button.setEnabled(True)
        self._basal_scanf_button.setEnabled(True)
        self._image_button.setEnabled(True)
        
        
    def _update_scanfield_parameters(self):
        
        # Add the default scanfield parameters
        
        self._dwelltime.setText(str(self._sf.dwelltime))
        self._flyback.setText(str(self._sf.frame_flyback))
        self._flytoline.setText(str(self._sf.flytoline))
        self._pixbin.setText(str(self._sf.pixel_bin_factor))
        self._samplerate.setText(str(self._sf.sampling_rate))
        self._fillfraction.setText(str(self._sf.fill_fraction))
        
        
    def _plot_image(self):
        
        self._selected_z = 0
        self._selected_ch = 0
        self._imv.setImage(self._stack.image()[self._selected_z, self._selected_ch, :, :])
        
        self._z_slider.setEnabled(True)
        self._z_slider.setRange(0, self._stack.nSlices - 1)
        self._z_slider.setTickInterval(1)
        self._z_slider.setTickPosition(QSlider.TicksBelow)
        self._imv_layout.addWidget(self._z_slider, 1, 0, 1, -1)
        
        self._channel_slider.setEnabled(True)
        self._channel_slider.setRange(0, self._stack.nChannels - 1)
        self._channel_slider.setTickInterval(1)
        self._channel_slider.setTickPosition(QSlider.TicksBelow)
        self._imv_layout.addWidget(self._channel_slider, 3, 0, 1, -1)

        self._is_image_plot = True
        self._clear_image_button.setEnabled(True)
        
        
    def _update_image(self):
        
        layer = self._z_slider.value()
        channel = self._channel_slider.value()
        self._imv.setImage(self._stack.image()[layer, channel, :, :])
        
        
    def _clear_image(self):
        
        self._imv.setImage(np.empty((0, 0), dtype=np.uint8))
        self._z_slider.setEnabled(False)
        self._channel_slider.setEnabled(False)
        self._is_image_plot = False
        self._clear_image_button.setEnabled(False)

    def _on_closing(self):
        
        reply = QMessageBox.question(self, 'Quit', 'Do you want to quit?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # User confirmed to quit
            QApplication.quit()
        

def main():
    app = QApplication([])  # Create a PyQt5 application instance
    window = GUI()  # Create an instance of your GUI class
    window.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()
        
