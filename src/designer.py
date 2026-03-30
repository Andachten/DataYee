# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("DataYee")
        
        screen = QtWidgets.QApplication.desktop().screenGeometry()
        width = min(1400, screen.width() * 0.9)
        height = min(900, screen.height() * 0.9)
        MainWindow.resize(int(width), int(height))
        
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        MainWindow.setFont(font)
        
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./src/ui/resources/DataYee.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        MainWindow.setCentralWidget(self.centralwidget)
        
        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        
        self._create_control_panel()
        self._create_plot_area()
        self._create_menubar(MainWindow)
        self._create_statusbar(MainWindow)
        
        self.main_layout.addWidget(self.groupBox_11)
        self.main_layout.addWidget(self.splitter)
        
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
    
    def _create_control_panel(self):
        self.groupBox_11 = QtWidgets.QGroupBox()
        self.groupBox_11.setObjectName("groupBox_11")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox_11)
        self.horizontalLayout.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout.setSpacing(10)
        
        self._create_wlc_group()
        self._create_navigation_group()
        self._create_action_group()
        
        self.horizontalLayout.addStretch(1)
    
    def _create_wlc_group(self):
        self.groupBox_6 = QtWidgets.QGroupBox()
        self.groupBox_6.setObjectName("groupBox_6")
        grid = QtWidgets.QGridLayout(self.groupBox_6)
        grid.setContentsMargins(5, 5, 5, 5)
        grid.setSpacing(5)
        
        self.label_2 = QtWidgets.QLabel("Lc")
        self.label_2.setObjectName("label_2")
        grid.addWidget(self.label_2, 0, 0, 1, 1)
        
        self.lcdoubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.lcdoubleSpinBox.setDecimals(1)
        self.lcdoubleSpinBox.setSingleStep(0.5)
        self.lcdoubleSpinBox.setProperty("value", 1.0)
        self.lcdoubleSpinBox.setObjectName("lcdoubleSpinBox")
        self.lcdoubleSpinBox.setMaximumWidth(80)
        grid.addWidget(self.lcdoubleSpinBox, 0, 1, 1, 1)
        
        self.lcslide = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.lcslide.setMinimum(-50)
        self.lcslide.setMaximum(50)
        self.lcslide.setProperty("value", 0)
        self.lcslide.setTracking(True)
        self.lcslide.setObjectName("lcslide")
        self.lcslide.setMaximumWidth(150)
        grid.addWidget(self.lcslide, 0, 2, 1, 1)
        
        self.label_3 = QtWidgets.QLabel("Lp")
        self.label_3.setObjectName("label_3")
        grid.addWidget(self.label_3, 1, 0, 1, 1)
        
        self.lpdoubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.lpdoubleSpinBox.setMaximum(0.1)
        self.lpdoubleSpinBox.setSingleStep(0.005)
        self.lpdoubleSpinBox.setProperty("value", 0.01)
        self.lpdoubleSpinBox.setObjectName("lpdoubleSpinBox")
        self.lpdoubleSpinBox.setMaximumWidth(80)
        grid.addWidget(self.lpdoubleSpinBox, 1, 1, 1, 1)
        
        self.lpslide = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.lpslide.setMinimum(-20)
        self.lpslide.setMaximum(20)
        self.lpslide.setPageStep(10)
        self.lpslide.setProperty("value", 0)
        self.lpslide.setObjectName("lpslide")
        self.lpslide.setMaximumWidth(150)
        grid.addWidget(self.lpslide, 1, 2, 1, 1)
        
        self.label_5 = QtWidgets.QLabel("k")
        self.label_5.setObjectName("label_5")
        grid.addWidget(self.label_5, 2, 0, 1, 1)
        
        self.kSpinBox = QtWidgets.QDoubleSpinBox()
        self.kSpinBox.setDecimals(3)
        self.kSpinBox.setProperty("value", 1.0)
        self.kSpinBox.setObjectName("kSpinBox")
        self.kSpinBox.setMaximumWidth(80)
        grid.addWidget(self.kSpinBox, 2, 1, 1, 1)
        
        self.kSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.kSlider.setMinimum(-20)
        self.kSlider.setMaximum(20)
        self.kSlider.setOrientation(QtCore.Qt.Horizontal)
        self.kSlider.setObjectName("kSlider")
        self.kSlider.setMaximumWidth(150)
        grid.addWidget(self.kSlider, 2, 2, 1, 1)
        
        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        grid.addWidget(self.comboBox, 0, 3, 1, 1)
        
        self.lclplabel = QtWidgets.QLabel()
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.lclplabel.setFont(font)
        self.lclplabel.setText("")
        self.lclplabel.setObjectName("lclplabel")
        grid.addWidget(self.lclplabel, 3, 0, 1, 4)
        
        self.horizontalLayout.addWidget(self.groupBox_6)
    
    def _create_navigation_group(self):
        self.groupBox_7 = QtWidgets.QGroupBox()
        self.groupBox_7.setObjectName("groupBox_7")
        vbox = QtWidgets.QVBoxLayout(self.groupBox_7)
        vbox.setContentsMargins(5, 5, 5, 5)
        
        self.label = QtWidgets.QLabel("Peak select:")
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName("label")
        vbox.addWidget(self.label)
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.setSpacing(5)
        
        self.leftButton = QtWidgets.QPushButton()
        self.leftButton.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("./src/ui/resources/left_arrow.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.leftButton.setIcon(icon1)
        self.leftButton.setIconSize(QtCore.QSize(40, 40))
        self.leftButton.setObjectName("leftButton")
        hbox.addWidget(self.leftButton)
        
        self.topButton = QtWidgets.QPushButton()
        self.topButton.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap("./src/ui/resources/top.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.topButton.setIcon(icon3)
        self.topButton.setIconSize(QtCore.QSize(40, 40))
        self.topButton.setObjectName("topButton")
        hbox.addWidget(self.topButton)
        
        self.downButton = QtWidgets.QPushButton()
        self.downButton.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap("./src/ui/resources/down.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.downButton.setIcon(icon2)
        self.downButton.setIconSize(QtCore.QSize(40, 40))
        self.downButton.setObjectName("downButton")
        hbox.addWidget(self.downButton)
        
        self.rightButton = QtWidgets.QPushButton()
        self.rightButton.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap("./src/ui/resources/right.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.rightButton.setIcon(icon4)
        self.rightButton.setIconSize(QtCore.QSize(40, 40))
        self.rightButton.setObjectName("rightButton")
        hbox.addWidget(self.rightButton)
        
        self.spinBox = QtWidgets.QSpinBox()
        self.spinBox.setMaximum(10000)
        self.spinBox.setSingleStep(10)
        self.spinBox.setObjectName("spinBox")
        hbox.addWidget(self.spinBox)
        
        vbox.addLayout(hbox)
        self.horizontalLayout.addWidget(self.groupBox_7)
    
    def _create_action_group(self):
        self.groupBox_8 = QtWidgets.QGroupBox()
        self.groupBox_8.setObjectName("groupBox_8")
        hbox = QtWidgets.QHBoxLayout(self.groupBox_8)
        hbox.setContentsMargins(5, 5, 5, 5)
        
        self.trashButtom = QtWidgets.QPushButton()
        self.trashButtom.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap("./src/ui/resources/trash.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.trashButtom.setIcon(icon5)
        self.trashButtom.setIconSize(QtCore.QSize(40, 40))
        self.trashButtom.setObjectName("trashButtom")
        hbox.addWidget(self.trashButtom)
        
        self.pushButton_2 = QtWidgets.QPushButton()
        self.pushButton_2.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap("./src/ui/resources/renew.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon6)
        self.pushButton_2.setIconSize(QtCore.QSize(40, 40))
        self.pushButton_2.setObjectName("pushButton_2")
        hbox.addWidget(self.pushButton_2)
        
        self.horizontalLayout.addWidget(self.groupBox_8)
    
    def _create_plot_area(self):
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        self.groupBox_10 = QtWidgets.QGroupBox()
        self.groupBox_10.setObjectName("groupBox_10")
        vbox = QtWidgets.QVBoxLayout(self.groupBox_10)
        vbox.setContentsMargins(5, 5, 5, 5)
        
        self.groupBox_9 = QtWidgets.QGroupBox()
        self.groupBox_9.setObjectName("groupBox_9")
        vbox1 = QtWidgets.QVBoxLayout(self.groupBox_9)
        self.usemodel_cb = QtWidgets.QCheckBox("USE MODEL")
        self.usemodel_cb.setTristate(False)
        self.usemodel_cb.setObjectName("usemodel_cb")
        vbox1.addWidget(self.usemodel_cb)
        self.fastmode = QtWidgets.QCheckBox("Fast Mode")
        self.fastmode.setObjectName("fastmode")
        vbox1.addWidget(self.fastmode)
        self.stickmodel = QtWidgets.QCheckBox("Strict")
        self.stickmodel.setObjectName("stickmodel")
        vbox1.addWidget(self.stickmodel)
        vbox.addWidget(self.groupBox_9)
        
        self.groupBox_2 = QtWidgets.QGroupBox("Task")
        self.groupBox_2.setObjectName("groupBox_2")
        vbox2 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.tasktype_cell = QtWidgets.QRadioButton("CELL CURVE")
        self.tasktype_cell.setObjectName("tasktype_cell")
        vbox2.addWidget(self.tasktype_cell)
        self.radioButton_2 = QtWidgets.QRadioButton("SMFS")
        self.radioButton_2.setChecked(True)
        self.radioButton_2.setObjectName("radioButton_2")
        vbox2.addWidget(self.radioButton_2)
        vbox.addWidget(self.groupBox_2)
        
        self.groupBox_3 = QtWidgets.QGroupBox("PeakNum")
        self.groupBox_3.setObjectName("groupBox_3")
        hbox3 = QtWidgets.QHBoxLayout(self.groupBox_3)
        self.spinBox_2 = QtWidgets.QSpinBox()
        self.spinBox_2.setMaximum(30)
        self.spinBox_2.setProperty("value", 1)
        self.spinBox_2.setObjectName("spinBox_2")
        hbox3.addWidget(self.spinBox_2)
        self.label_4 = QtWidgets.QLabel("-")
        self.label_4.setObjectName("label_4")
        hbox3.addWidget(self.label_4)
        self.spinBox_3 = QtWidgets.QSpinBox()
        self.spinBox_3.setMaximum(40)
        self.spinBox_3.setProperty("value", 6)
        self.spinBox_3.setObjectName("spinBox_3")
        hbox3.addWidget(self.spinBox_3)
        vbox.addWidget(self.groupBox_3)
        
        self.groupBox_4 = QtWidgets.QGroupBox("Mark")
        self.groupBox_4.setObjectName("groupBox_4")
        vbox4 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setObjectName("lineEdit")
        vbox4.addWidget(self.lineEdit)
        vbox.addWidget(self.groupBox_4)
        
        self.groupBox_5 = QtWidgets.QGroupBox("ZOOM")
        self.groupBox_5.setObjectName("groupBox_5")
        vbox5 = QtWidgets.QVBoxLayout(self.groupBox_5)
        hbox5 = QtWidgets.QHBoxLayout()
        self.zoomx = QtWidgets.QCheckBox("X")
        self.zoomx.setObjectName("zoomx")
        hbox5.addWidget(self.zoomx)
        self.zoomy = QtWidgets.QCheckBox("Y")
        self.zoomy.setObjectName("zoomy")
        hbox5.addWidget(self.zoomy)
        vbox5.addLayout(hbox5)
        self.zoomfix = QtWidgets.QCheckBox("Fix")
        self.zoomfix.setObjectName("zoomfix")
        vbox5.addWidget(self.zoomfix)
        vbox.addWidget(self.groupBox_5)
        
        self.pushButton = QtWidgets.QPushButton("Run")
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.pushButton.setFont(font)
        self.pushButton.setStyleSheet("QPushButton { color: black;}")
        self.pushButton.setObjectName("pushButton")
        vbox.addWidget(self.pushButton)
        
        vbox.addStretch(1)
        self.splitter.addWidget(self.groupBox_10)
        
        self.groupBox = QtWidgets.QGroupBox("Force Curve")
        self.groupBox.setObjectName("groupBox")
        self.splitter.addWidget(self.groupBox)
        
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
    
    def _create_menubar(self, MainWindow):
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setObjectName("menuBar")
        MainWindow.setMenuBar(self.menuBar)
        
        self.menu = QtWidgets.QMenu("File", self.menuBar)
        self.menuOpen = QtWidgets.QMenu("Open", self.menu)
        self.menuExport = QtWidgets.QMenu("Export", self.menu)
        self.menu.setObjectName("menu")
        self.menuOpen.setObjectName("menuOpen")
        self.menuExport.setObjectName("menuExport")
        
        self.menuEdit = QtWidgets.QMenu("Edit", self.menuBar)
        self.menuAction = QtWidgets.QMenu("Action", self.menuEdit)
        self.menuAction.setObjectName("menuAction")
        self.menuEdit.addAction(self.menuAction.menuAction())
        self.menuEdit.setObjectName("menuEdit")
        
        self.menuPlot = QtWidgets.QMenu("Plot", self.menuBar)
        self.menucontour_lenght = QtWidgets.QMenu("Contour length", self.menuPlot)
        self.menuAdhesion = QtWidgets.QMenu("Adhesion", self.menuPlot)
        self.menuStatistics = QtWidgets.QMenu("Statistics", self.menuPlot)
        self.menucontour_lenght.setObjectName("menucontour_lenght")
        self.menuAdhesion.setObjectName("menuAdhesion")
        self.menuStatistics.setObjectName("menuStatistics")
        self.menuPlot.addAction(self.menucontour_lenght.menuAction())
        self.menuPlot.addAction(self.menuAdhesion.menuAction())
        self.menuPlot.addAction(self.menuStatistics.menuAction())
        self.menuPlot.setObjectName("menuPlot")
        
        self.menuPliguin = QtWidgets.QMenu("Plugin", self.menuBar)
        self.menuEnergy_landscape = QtWidgets.QMenu("Energy landscape", self.menuPliguin)
        self.menuClustering = QtWidgets.QMenu("Clustering", self.menuPliguin)
        self.menuEnergy_landscape.setObjectName("menuEnergy_landscape")
        self.menuClustering.setObjectName("menuClustering")
        self.menuPliguin.addAction(self.menuEnergy_landscape.menuAction())
        self.menuPliguin.addAction(self.menuClustering.menuAction())
        self.menuPliguin.setObjectName("menuPliguin")
        
        self.menuAbout = QtWidgets.QMenu("About", self.menuBar)
        self.menuAbout.setObjectName("menuAbout")
        
        self._create_actions()
        self._populate_menus()
        
        self.menuBar.addAction(self.menu.menuAction())
        self.menuBar.addAction(self.menuEdit.menuAction())
        self.menuBar.addAction(self.menuPlot.menuAction())
        self.menuBar.addAction(self.menuPliguin.menuAction())
        self.menuBar.addAction(self.menuAbout.menuAction())
    
    def _create_actions(self):
        self.actionSave = QtWidgets.QAction("Save")
        self.actionSave.setShortcut("Ctrl+S")
        self.actionSave.setObjectName("actionSave")
        
        self.actionForce_Curve = QtWidgets.QAction("Force Curve")
        self.actionForce_Curve.setShortcut("Ctrl+O")
        self.actionForce_Curve.setObjectName("actionForce_Curve")
        
        self.actionBatch_of_Force_Curve = QtWidgets.QAction("Batch of Force Curve")
        self.actionBatch_of_Force_Curve.setCheckable(True)
        self.actionBatch_of_Force_Curve.setObjectName("actionBatch_of_Force_Curve")
        
        self.actionSave_as = QtWidgets.QAction("Save as")
        self.actionSave_as.setObjectName("actionSave_as")
        
        self.actionDataYee_Force = QtWidgets.QAction("DataYee-Force")
        self.actionDataYee_Force.setObjectName("actionDataYee_Force")
        
        self.actiontxt = QtWidgets.QAction("Txt")
        self.txt_action = QtWidgets.QAction("Txt")
        self.txt_action.setObjectName("actiontxt")
        
        self.actionexcel = QtWidgets.QAction("Excel")
        self.actionexcel.setObjectName("actionexcel")
        
        self.actionfigure = QtWidgets.QAction("Figure")
        self.actionfigure.setObjectName("actionfigure")
        
        self.actionbatch_of_txt = QtWidgets.QAction("Batch of txt")
        self.actionbatch_of_txt.setObjectName("actionbatch_of_txt")
        
        self.actionExit = QtWidgets.QAction("Exit")
        self.actionExit.setObjectName("actionExit")
        
        self.actionhelp = QtWidgets.QAction("Help")
        self.actionhelp.setObjectName("actionhelp")
        
        self.actionDataYee = QtWidgets.QAction("DataYee")
        self.actionDataYee.setObjectName("actionDataYee")
        
        self.actionUpdate = QtWidgets.QAction("Update")
        self.actionUpdate.setObjectName("actionUpdate")
        
        self.actionDelete = QtWidgets.QAction("Delete")
        self.actionDelete.setShortcut("Del")
        self.actionDelete.setObjectName("actionDelete")
        
        self.actionBaseline_plus = QtWidgets.QAction("Baseline plus")
        self.actionBaseline_plus.setShortcut("Ctrl+=")
        self.actionBaseline_plus.setObjectName("actionBaseline_plus")
        
        self.actionBaseline_minus = QtWidgets.QAction("Baseline minus")
        self.actionBaseline_minus.setShortcut("Ctrl+-")
        self.actionBaseline_minus.setObjectName("actionBaseline_minus")
        
        self.actionHistgram = QtWidgets.QAction("Histogram")
        self.actionHistgram.setObjectName("actionHistgram")
        
        self.actionScatter = QtWidgets.QAction("Scatter")
        self.actionScatter.setObjectName("actionScatter")
        
        self.actionMap = QtWidgets.QAction("Map")
        self.actionMap.setObjectName("actionMap")
        
        self.actionHistogram = QtWidgets.QAction("Histogram")
        self.actionHistogram.setObjectName("actionHistogram")
        
        self.actionpeakindex_plus = QtWidgets.QAction("Peakindex plus")
        self.actionpeakindex_plus.setShortcut("+")
        self.actionpeakindex_plus.setObjectName("actionpeakindex_plus")
        
        self.actionpeakindex_minus = QtWidgets.QAction("Peakindex minus")
        self.actionpeakindex_minus.setShortcut("_")
        self.actionpeakindex_minus.setObjectName("actionpeakindex_minus")
        
        self.actioncopy_peak = QtWidgets.QAction("Copy peak")
        self.actioncopy_peak.setShortcut("Ctrl+C")
        self.actioncopy_peak.setObjectName("actioncopy_peak")
        
        self.actionparameters_setting = QtWidgets.QAction("Parameters setting")
        self.actionparameters_setting.setShortcut("Ctrl+P")
        self.actionparameters_setting.setObjectName("actionparameters_setting")
        
        self.actionmark_base_on_dlc = QtWidgets.QAction("Mark base on dlc")
        self.actionmark_base_on_dlc.setObjectName("actionmark_base_on_dlc")
        
        self.actionBell_Evans = QtWidgets.QAction("Bell Evans")
        self.actionBell_Evans.setObjectName("actionBell_Evans")
        
        self.actionFriddle = QtWidgets.QAction("Friddle")
        self.actionFriddle.setObjectName("actionFriddle")
        
        self.actionSort_by_similarity = QtWidgets.QAction("Sort by similarity")
        self.actionSort_by_similarity.setObjectName("actionSort_by_similarity")
        
        self.actionClustering_by_KMeans = QtWidgets.QAction("Clustering by KMeans")
        self.actionClustering_by_KMeans.setObjectName("actionClustering_by_KMeans")
        
        self.actionHistogram_scatter = QtWidgets.QAction("Histogram_scatter")
        self.actionHistogram_scatter.setObjectName("actionHistogram_scatter")
        
        self.actionScript = QtWidgets.QAction("Script")
        self.actionScript.setObjectName("actionScript")
        
        self.actionData_equipment = QtWidgets.QAction("Data equipment")
        self.actionData_equipment.setObjectName("actionData_equipment")
        
        self.actionData_slimming = QtWidgets.QAction("Data slimming")
        self.actionData_slimming.setObjectName("actionData_slimming")
    
    def _populate_menus(self):
        self.menuOpen.addAction(self.actionForce_Curve)
        self.menuOpen.addAction(self.actionBatch_of_Force_Curve)
        self.menuOpen.addAction(self.actionDataYee_Force)
        
        self.menuExport.addAction(self.actiontxt)
        self.menuExport.addAction(self.actionexcel)
        self.menuExport.addAction(self.actionfigure)
        self.menuExport.addAction(self.actionbatch_of_txt)
        
        self.menu.addAction(self.menuOpen.menuAction())
        self.menu.addAction(self.actionSave)
        self.menu.addAction(self.actionSave_as)
        self.menu.addAction(self.menuExport.menuAction())
        self.menu.addAction(self.actionData_equipment)
        self.menu.addAction(self.actionData_slimming)
        self.menu.addSeparator()
        self.menu.addAction(self.actionExit)
        
        self.menuAction.addAction(self.actionDelete)
        self.menuAction.addAction(self.actionBaseline_plus)
        self.menuAction.addAction(self.actionBaseline_minus)
        self.menuAction.addAction(self.actionpeakindex_plus)
        self.menuAction.addAction(self.actionpeakindex_minus)
        self.menuAction.addAction(self.actioncopy_peak)
        
        self.menuEdit.addAction(self.actionparameters_setting)
        self.menuEdit.addAction(self.actionmark_base_on_dlc)
        self.menuEdit.addAction(self.menuAction.menuAction())
        
        self.menucontour_lenght.addAction(self.actionHistgram)
        self.menucontour_lenght.addAction(self.actionScatter)
        self.menuAdhesion.addAction(self.actionMap)
        self.menuAdhesion.addAction(self.actionHistogram)
        self.menuStatistics.addAction(self.actionHistogram_scatter)
        
        self.menuEnergy_landscape.addAction(self.actionBell_Evans)
        self.menuEnergy_landscape.addAction(self.actionFriddle)
        self.menuClustering.addAction(self.actionClustering_by_KMeans)
        self.menuClustering.addAction(self.actionSort_by_similarity)
        
        self.menuPliguin.addAction(self.menuEnergy_landscape.menuAction())
        self.menuPliguin.addAction(self.menuClustering.menuAction())
        self.menuPliguin.addAction(self.actionScript)
        
        self.menuAbout.addAction(self.actionhelp)
        self.menuAbout.addAction(self.actionDataYee)
        self.menuAbout.addAction(self.actionUpdate)
    
    def _create_statusbar(self, MainWindow):
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
    
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        self.comboBox.setItemText(0, _translate("MainWindow", "None"))
        self.comboBox.setItemText(1, _translate("MainWindow", "Fix lc"))
        self.actiontxt.setText(_translate("MainWindow", "Txt"))
        self.txt_action.setText(_translate("MainWindow", "Txt"))
