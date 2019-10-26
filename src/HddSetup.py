# for localized messages
from . import _
from enigma import *
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Tools.LoadPixmap import LoadPixmap
from Components.Button import Button
from Components.Label import Label
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Standby import TryQuitMainloop
from HddPartitions import HddPartitions
from HddInfo import HddInfo
from Disks import Disks
from ExtraMessageBox import ExtraMessageBox
from ExtraActionBox import ExtraActionBox
from MountPoints import MountPoints
import os

sfdisk = os.path.exists('/usr/sbin/sfdisk')

def DiskEntry(model, size, removable, rotational, internal):
	if not removable and internal and rotational:
		picture = LoadPixmap(cached = True, path = resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/DeviceManager/icons/disk.png"))
	elif internal and not rotational:
		picture = LoadPixmap(cached = True, path = resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/DeviceManager/icons/ssddisk.png"))
	else:
		picture = LoadPixmap(cached = True, path = resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/DeviceManager/icons/diskusb.png"))
	return (picture, model, size)

class HddSetup(Screen):

	skin = """
		<screen name="HddSetup" position="center,center" size="560,430" title="Hard Drive Setup">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget source="menu" render="Listbox" position="20,45" size="520,380" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
						MultiContentEntryPixmapAlphaTest(pos = (5, 0), size = (48, 48), png = 0),
						MultiContentEntryText(pos = (65, 10), size = (330, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),
						MultiContentEntryText(pos = (405, 10), size = (125, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 2),
						],
						"fonts": [gFont("Regular", 22)],
						"itemHeight": 50
					}
				</convert>
			</widget>
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		self.setTitle(_("Storage device manager"))
		self.disks = list()
		self.mdisks = Disks()
		self.asHDD = False
		for disk in self.mdisks.disks:
			capacity = "%d MB" % (disk[1] / (1024 * 1024))
			self.disks.append(DiskEntry(disk[3], capacity, disk[2], disk[6], disk[7]))
		self["menu"] = List(self.disks)
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button(_("Info"))
		if sfdisk:
			self["key_yellow"] = Button(_("Initialize"))
		else:
			self["key_yellow"] = Button("")
		self["key_blue"] = Button(_("Partitions"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"blue": self.blue,
			"yellow": self.yellow,
			"green": self.green,
			"red": self.close,
			"cancel": self.close,
		}, -2)

	def isExt4Supported(self):
		return "ext4" in open("/proc/filesystems").read()

	def mkfs(self):
		self.formatted += 1
		return self.mdisks.mkfs(self.mdisks.disks[self.sindex][0], self.formatted, self.fsresult)

	def refresh(self):
		self.disks = list()
		self.mdisks = Disks()
		for disk in self.mdisks.disks:
			capacity = "%d MB" % (disk[1] / (1024 * 1024))
			self.disks.append(DiskEntry(disk[3], capacity, disk[2], disk[6], disk[7]))

		self["menu"].setList(self.disks)

	def checkDefault(self):
		mp = MountPoints()
		mp.read()
		if self.asHDD and not mp.exist("/media/hdd"):
			mp.add(self.mdisks.disks[self.sindex][0], 1, "/media/hdd")
			mp.write()
			mp.mount(self.mdisks.disks[self.sindex][0], 1, "/media/hdd")
			os.system("mkdir -p /media/hdd/movie")
			msg = _("Initializing fixed mounted drive requires a system restart in order to take effect. ")
			msg += _("Do you want to restart your receiver now?")
			self.session.openWithCallback(self.restartBox, MessageBox, msg, MessageBox.TYPE_YESNO, title=_("Restart receiver"))

	def restartBox(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 2)

	def format(self, result):
		if result != 0:
			msg = _("Formatting partition %d failed!") % (self.formatted)
			self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)
		if self.result == 0:
			if self.formatted > 0:
				self.checkDefault()
				self.refresh()
				return
		elif self.result > 0 and self.result < 3:
			if self.formatted > 1:
				self.checkDefault()
				self.refresh()
				return
		elif self.result == 3:
			if self.formatted > 2:
				self.checkDefault()
				self.refresh()
				return
		elif self.result == 4:
			if self.formatted > 3:
				self.checkDefault()
				self.refresh()
				return
		msg = _("Formatting partition %d") % (self.formatted + 1)
		self.session.openWithCallback(self.format, ExtraActionBox, msg, _("Initialize disk"), self.mkfs)

	def fdiskEnded(self, result):
		if result == 0:
			self.format(0)
		elif result == -1:
			msg = _("Unmounting current drive failed! ")
			msg += _("A recording in progress, timeshift or some external tools (like samba, swapfile and nfsd) may cause this problem. ")
			msg += _("Please stop these processes or applications and try again.")
			self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)
		else:
			self.session.open(MessageBox, _("Partitioning failed!"), MessageBox.TYPE_ERROR)

	def fdisk(self):
		return self.mdisks.fdisk(self.mdisks.disks[self.sindex][0], self.mdisks.disks[self.sindex][1], self.result, self.fsresult)

	def initialize(self, result):
		if not self.isExt4Supported():
			result += 1
		if result != 6:
			self.fsresult = result
			self.formatted = 0
			mp = MountPoints()
			mp.read()
			mp.deleteDisk(self.mdisks.disks[self.sindex][0])
			mp.write()
			self.session.openWithCallback(self.fdiskEnded, ExtraActionBox, _("Partitioning..."), _("Initialize disk"), self.fdisk)

	def chooseFSType(self, result):
		if result != 5:
			self.result = result
			if self.isExt4Supported():
				self.session.openWithCallback(self.initialize, ExtraMessageBox, _("Format as"), _("Partitioner"),
											[ [ "Ext4", "partitionmanager.png" ],
											[ "Ext3", "partitionmanager.png" ],
											[ "Ext2", "partitionmanager.png" ],
											[ "NTFS", "partitionmanager.png" ],
											[ "exFAT", "partitionmanager.png" ],
											[ "Fat32", "partitionmanager.png" ],
											[ _("Cancel"), "cancel.png" ],
											], 1, 6)
			else:
				self.session.openWithCallback(self.initialize, ExtraMessageBox, _("Format as"), _("Partitioner"),
											[ [ "Ext3", "partitionmanager.png" ],
											[ "Ext2", "partitionmanager.png" ],
											[ "NTFS", "partitionmanager.png" ],
											[ "exFAT", "partitionmanager.png" ],
											[ "Fat32", "partitionmanager.png" ],
											[ _("Cancel"), "cancel.png" ],
											], 1, 5)
	def yellow(self):
		self.asHDD = False
		if sfdisk and len(self.mdisks.disks) > 0:
			list = [(_("No - simple"), "simple"), (_("Yes - fstab entry as /media/hdd"), "as_hdd")]
			def extraOption(ret):
				if ret:
					if ret[1] == "as_hdd":
						self.asHDD = True
					self.yellowAnswer()
			self.session.openWithCallback(extraOption, ChoiceBox, title=_("Initialize as HDD?"), list=list)

	def yellowAnswer(self):
		if sfdisk and len(self.mdisks.disks) > 0:
			self.sindex = self['menu'].getIndex()
			msg = _("Please select your preferred configuration. ")
			msg += _("Alternatively you can use the standard 'Hard disk setup' to initialize your drive in ext4.")
			self.session.openWithCallback(self.chooseFSType, ExtraMessageBox, msg, _("Partitioner"),
										[ [ _("One partition"), "partitionmanager.png" ],
										[ _("Two partitions") + " (50% - 50%)", "partitionmanager.png" ],
										[ _("Two partitions") + " (75% - 25%)", "partitionmanager.png" ],
										[ _("Three partitions") + " (33% - 33% - 33%)", "partitionmanager.png" ],
										[ _("Four partitions") + " (25% - 25% - 25% - 25%)", "partitionmanager.png" ],
										[ _("Cancel"), "cancel.png" ],
										], 1, 5)

	def green(self):
		if len(self.mdisks.disks) > 0:
			self.sindex = self['menu'].getIndex()
			self.session.open(HddInfo, self.mdisks.disks[self.sindex][0], self.mdisks.disks[self.sindex])

	def blue(self):
		if len(self.mdisks.disks) > 0:
			self.sindex = self['menu'].getIndex()
			if len(self.mdisks.disks[self.sindex][5]) == 0:
				msg = _("You need to initialize your storage device first.")
				self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)
			else:
				self.session.open(HddPartitions, self.mdisks.disks[self.sindex])
