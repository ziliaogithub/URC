import os
import rospkg

import actionlib
import rospy
import rover_panorama.msg
import rover_science.msg
import rover_science.srv
import std_srvs.srv
from python_qt_binding import loadUi
from python_qt_binding.QtCore import Signal, Slot
from python_qt_binding.QtWidgets import QWidget, QInputDialog, QTableWidgetItem
from python_qt_binding.QtGui import QPixmap


class PluginWidget(QWidget):
    pstate_signal = Signal(rover_panorama.msg.PanoState)
    progreeeeeees = Signal(rover_panorama.msg.PanoramaFeedback)
    finiiiiiished = Signal(rover_panorama.msg.PanoramaResult)
    sstate_signal = Signal(dict)

    def __init__(self):
        super(PluginWidget, self).__init__()
        ui_file = os.path.join(rospkg.RosPack().get_path('rover_rqt_science'), 'resource', 'pano.ui')
        loadUi(ui_file, self)
        self.files = {}
        self.science_mark = -1
        self.pixmaps = {}
        self.sites = {}

        self.mark_pano = rospy.ServiceProxy("/science/sci/mark_panorama", rover_science.srv.MarkPano)
        self.panorama = actionlib.SimpleActionClient("/science/panorama/stitch_panorama", rover_panorama.msg.PanoramaAction)
        self.take_pano_image = rospy.ServiceProxy("/science/panorama/take_pano_image", std_srvs.srv.Empty)

        def state_sub(s):
            self.pstate_signal.emit(s)

        self._state_sub = rospy.Subscriber("/science/panorama/pano_state", rover_panorama.msg.PanoState, callback=state_sub)

        def science_sub(s):
            self.sstate_signal.emit({x.site_name: j for j, x in enumerate(s.sites)})

        self._sstate_sub = rospy.Subscriber("/science/sites", rover_science.msg.Sites, callback=science_sub)

        self.progreeeeeees.connect(self.new_feedback)
        self.finiiiiiished.connect(self.goaal)
        self.pstate_signal.connect(self.new_pano_state)
        self.sstate_signal.connect(self.new_state)

        self.pushButton.clicked.connect(self.push_button)
        self.stitchButton.clicked.connect(self.stitch)
        self.tableWidget.cellClicked.connect(self.new_selected)

    def feedback(self, f):
        self.progreeeeeees.emit(f)

    def goal(self, f, r):
        self.finiiiiiished.emit(r)
        # print "GGAGAGG"

    @Slot(dict)
    def new_state(self, l):
        self.sites = l

    @Slot(rover_panorama.msg.PanoState)
    def new_pano_state(self, msg):
        self.tableWidget.clearContents()
        self.files = {}
        self.pixmaps = {}
        j = 0
        self.tableWidget.setRowCount(len(msg.in_transfer) + len(msg.transferred))
        for i in msg.in_transfer:
            self.tableWidget.setItem(j, 0, QTableWidgetItem(i))
            self.tableWidget.setItem(j, 1, QTableWidgetItem("Transferring"))
            j += 1
            # self.tableWidget.setRowCount(j)
        for i in msg.transferred:
            self.tableWidget.setItem(j, 0, QTableWidgetItem(i))
            self.tableWidget.setItem(j, 1, QTableWidgetItem("Transferred"))
            self.files[j] = i
            print self.files
            self.pixmaps[j] = QPixmap(i)
            j += 1

    @Slot(int, int)
    def new_selected(self, r, c):
        print r, c
        print self.pixmaps.keys()
        self.label.clear()
        if r in self.pixmaps.keys():
            print "GA"
            pmap = self.pixmaps[r]
            self.label.setPixmap(pmap)
            self.label.setScaledContents(True)
            self.label.setMaximumSize(400, 200)
            self.label.setText("")
        else:
            print "GA2"
            #self.label.setPixmap()
            self.label.setText("File does not exist yet")

    @Slot(rover_panorama.msg.PanoramaFeedback)
    def new_feedback(self, msg):
        c = 8 - msg.commandsToGo
        self.progressBar.setValue(c)

    @Slot(rover_panorama.msg.PanoramaGoal)
    def goaal(self, msg):
        request = rover_science.srv.MarkPanoRequest()
        request.mark_flags = request.HAS_PANO
        request.pano_location = msg.resultFilenameSmall
        self.mark_pano(request)

    @Slot()
    def push_button(self):
        try:
            self.take_pano_image(std_srvs.srv.EmptyRequest())
        except:
            pass

    @Slot()
    def stitch(self):
        site, ok = QInputDialog.getItem(self, "Pick a site", "Pick a site to set the panorama for", self.sites.keys())
        if not ok:
            return
        s = self.sites[site]
        self.science_mark = s
        self.panorama.send_goal(rover_panorama.msg.PanoramaGoal(), self.goal, None, self.feedback)
