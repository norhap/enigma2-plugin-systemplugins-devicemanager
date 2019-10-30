# for localized messages
from . import _
from enigma import *
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN, SCOPE_CURRENT_SKIN
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Tools.LoadPixmap import LoadPixmap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.Standby import TryQuitMainloop
from HddPartitions import HddPartitions
from HddInfo import HddInfo
from Disks import Disks
from ExtraActionBox import ExtraActionBox
from MountPoints import MountPoints
import os

sfdisk = os.path.exists('/usr/sbin/sfdisk')

def DiskEntry(model, size, removable, rotational, internal):
	if not removable and internal and rotational:
		icon = "disk-hdd"
	elif internal and not rotational:
		icon = "disk-ssd"
	else:
		icon = "disk-usb"
	picture = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "icons/DeviceManager/%s.png" % icon))
	if picture is None:
		picture = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/DeviceManager/icons/%s.png" % icon))
	return (picture, model, size)

class HddSetup(Screen):

	skin = """
		<screen name="HddSetup" position="center,center" size="560,430" title="Hard Drive Setup">
			<ePixmap pixmap="buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
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
		self.disks = []
		self.mdisks = Disks()
		self.asHDD = False
		for disk in self.mdisks.disks:
			capacity = "%.1f GB" % (disk[1] / 1073741824.0) # 1024 * 1024 * 1024
			self.disks.append(DiskEntry(disk[3], capacity, disk[2], disk[6], disk[7]))
		self["menu"] = List(self.disks)
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Info"))
		self["key_yellow"] = StaticText("")
		if sfdisk:
			self["key_yellow"] = StaticText(_("Initialize"))
		self["key_blue"] = StaticText(_("Partitions"))
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
		self.disks = []
		self.mdisks = Disks()
		for disk in self.mdisks.disks:
			capacity = "%.1f GB" % (disk[1] / 1073741824.0) # 1024 * 1024 * 1024
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
			msg = _("Initialization of fixed mounted drives require a system restart. ")
			msg += _("Do you want to restart your receiver now?")
			self.session.openWithCallback(self.restartBox, MessageBox, msg, title=_("Restart receiver"))

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
		self.session.openWithCallback(self.format, ExtraActionBox, msg, _("Disk initialization"), self.mkfs)

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
		if result is not None:
			self.fsresult = int(result[1])
			self.formatted = 0
			mp = MountPoints()
			mp.read()
			mp.deleteDisk(self.mdisks.disks[self.sindex][0])
			mp.write()
			self.session.openWithCallback(self.fdiskEnded, ExtraActionBox, _("Partitioning..."), _("Initialize disk"), self.fdisk)

	def chooseFSType(self, result):
		if result is not None:
			self.result = int(result[1])
			choicelist = [("Ext3", "1"), ("Ext2", "2"), ("NTFS", "3"), ("exFAT", "4"), ("Fat32", "5")]
			if self.isExt4Supported():
				choicelist.insert(0, ("Ext4", "0"))
			self.session.openWithCallback(self.initialize, ChoiceBox, title=_("Please select a file system for the drive"), list=choicelist)

	def yellowAnswer(self):
		if sfdisk and len(self.mdisks.disks) > 0:
			self.sindex = self['menu'].getIndex()
			choicelist = [(_("One partition"), "0")]
			choicelist.append((_("Two partitions") + " (50% - 50%)", "1"))
			choicelist.append((_("Two partitions") + " (75% - 25%)", "2"))
			choicelist.append((_("Three partitions") + " (33% - 33% - 33%)", "3"))
			choicelist.append((_("Four partitions") + " (25% - 25% - 25% - 25%)", "4"))
			self.session.openWithCallback(self.chooseFSType, ChoiceBox, title=_("Please select your preferred configuration"), list=choicelist)

	def yellow(self):
		if sfdisk and len(self.mdisks.disks) > 0:
			choicelist = [(_("no"), "no"), (_("yes"), "yes")] # use custom list to have control over the return values
			def extraOption(result):
				if result is not False:
					if result == "yes":
						self.asHDD = True
					else:
						self.asHDD = False
					self.yellowAnswer()
			self.session.openWithCallback(extraOption, MessageBox, _("Initialize as hard disk?"), simple=True, list=choicelist)

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
