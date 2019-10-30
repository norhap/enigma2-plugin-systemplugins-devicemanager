# for localized messages
from . import _
from enigma import *
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
from Tools.LoadPixmap import LoadPixmap
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Disks import Disks
from ExtraActionBox import ExtraActionBox
from MountPoints import MountPoints
from HddMount import HddMountDevice
import os

sfdisk = os.path.exists('/usr/sbin/sfdisk')

def PartitionEntry(description, size):
	picture = LoadPixmap(cached = True, path = resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/DeviceManager/icons/partitionmanager.png"))

	return (picture, description, size)

class HddPartitions(Screen):

	skin = """
		<screen name="HddPartitions" position="center,center" size="560,430" title="Hard Drive Partitions">
			<ePixmap pixmap="buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget name="label_disk" position="20,45" font="Regular;20" halign="center" size="520,25" valign="center" />
			<widget source="menu" render="Listbox" position="20,75" size="520,350" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
						MultiContentEntryPixmapAlphaTest(pos = (5, 0), size = (48, 48), png = 0),
						MultiContentEntryText(pos = (65, 10), size = (360, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),
						MultiContentEntryText(pos = (435, 10), size = (125, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 2),
						],
						"fonts": [gFont("Regular", 18)],
						"itemHeight": 50
					}
				</convert>
			</widget>
		</screen>"""

	def __init__(self, session, disk):
		Screen.__init__(self, session)
		self.setTitle(_("Partitions"))
		self.disk = disk

		self["menu"] = List([])
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText("")
		self["label_disk"] = Label("%s - %s" % (self.disk[0], self.disk[3]))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"red": self.close,
			"yellow": self.yellow,
			"green": self.green,
			"blue": self.blue,
			"cancel": self.close,
		}, -2)

		self.refreshMP()
		self["menu"].onSelectionChanged.append(self.selectionChanged)

	def selectionChanged(self):
		self["key_green"].setText("")
		self["key_yellow"].setText("")
		self["key_blue"].setText("")

		if len(self.disk[5]) > 0:
			index = self["menu"].getIndex() or 0
			if self.disk[5][index][3] == "83" or self.disk[5][index][3] == "7" or self.disk[5][index][3] == "b" or self.disk[5][index][3] == "c":
				self["key_green"].setText(_("Check"))
				if sfdisk:
					self["key_yellow"].setText(_("Format"))
				mp = self.mountpoints.get(self.disk[0], index+1)
				rmp = self.mountpoints.getRealMount(self.disk[0], index+1)
				if len(mp) > 0 or len(rmp) > 0:
					self.mounted = True
					self["key_blue"].setText(_("Unmount"))
				else:
					self.mounted = False
					self["key_blue"].setText(_("Mount"))

	def chkfs(self):
		disks = Disks()
		ret = disks.chkfs(self.disk[5][self.index][0][:3], self.index + 1, self.fstype)
		if ret == 0:
			msg = _("Disk check completed successfully.")
			self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
		elif ret == -1:
			msg = _("Unmounting current drive failed! ")
			msg += _("A recording in progress, timeshift or some external tools (like samba, swapfile and nfsd) may cause this problem. ")
			msg += _("Please stop these processes or applications and try again.")
			self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)
		else:
			msg = _("Error checking disk. ")
			msg += _("The disk may be damaged!")
			self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)

	def mkfs(self):
		disks = Disks()
		ret = disks.mkfs(self.disk[5][self.index][0][:3], self.index + 1, self.fstype)
		if ret == 0:
			msg = _("Format completed successfully.")
			self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
		elif ret == -2:
			msg = _("Formatting current drive failed! ")
			msg += _("A recording in progress, timeshift or some external tools (like samba, swapfile and nfsd) may cause this problem. ")
			msg += _("Please stop these processes or applications and try again.")
			self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)
		else:
			msg = _("Error formatting disk. ")
			msg += _("The disk may be damaged!")
			self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)

	def isExt4Supported(self):
		return "ext4" in open("/proc/filesystems").read()

	def green(self):
		if len(self.disk[5]) > 0:
			index = self["menu"].getIndex()
			if self.disk[5][index][3] == "83" or self.disk[5][index][3] == "7" or self.disk[5][index][3] == "b" or self.disk[5][index][3] == "c":
				self.index = index
				if self.disk[5][index][3] == "83":
					self.fstype = 0
				elif self.disk[5][index][3] == "7":
					self.fstype = 2
				elif self.disk[5][index][3] == "b" or self.disk[5][index][3] == "c":
					self.fstype = 3
				msg = _("Checking disk %s") % self.disk[5][index][0]
				self.session.open(ExtraActionBox, msg, _("Disk check"), self.chkfs)

	def yellow(self):
		if sfdisk and len(self.disk[5]) > 0:
			self.index = self["menu"].getIndex()
			choicelist = []
			if self.disk[5][self.index][3] == "83":
				choicelist = [("Ext3", "1"), ("Ext2", "2")]
				if self.isExt4Supported():
					choicelist.insert(0, ("Ext4", "0"))
			elif self.disk[5][self.index][3] == "7":
				choicelist = [("NTFS", "3"), ("exFAT", "4")]
			elif self.disk[5][self.index][3] == "b" or self.disk[5][self.index][3] == "c":
				choicelist = [("Fat32", "5")]

			def domkfs(result):
				if result is not None:
					self.fstype = int(result[1])
					msg = _("Formatting disk %s") % self.disk[5][self.index][0]
					self.session.open(ExtraActionBox, msg, _("Disk format"), self.mkfs)

			self.session.openWithCallback(domkfs, ChoiceBox, title=_("Please select a file system for the partition"), list=choicelist)

	def refreshMP(self):
		self.partitions = []
		self.mountpoints = MountPoints()
		self.mountpoints.read()
		count = 1
		for part in self.disk[5]:
			capacity = "%.1f GB" % (part[1] / 1073741824.0) # 1024 * 1024 * 1024
			mp = self.mountpoints.get(self.disk[0], count)
			rmp = self.mountpoints.getRealMount(self.disk[0], count)
			if len(mp) > 0:
				self.partitions.append(PartitionEntry(_("Partition {0} - {1} (fixed mounted: {2})").format(count, part[2], mp), capacity))
			elif len(rmp) > 0:
				self.partitions.append(PartitionEntry(_("Partition {0} - {1} (fast mounted: {2})").format(count, part[2], rmp), capacity))
			else:
				self.partitions.append(PartitionEntry(_("Partition {0} - {1}").format(count, part[2]), capacity))
			count += 1

		self["menu"].setList(self.partitions)
		self.selectionChanged()

	def blue(self):
		if len(self.disk[5]) > 0:
			index = self["menu"].getIndex()
			if self.disk[5][index][3] != "83" and self.disk[5][index][3] != "7" and self.disk[5][index][3] != "b" and self.disk[5][index][3] != "c":
				return

		if len(self.partitions) > 0:
			self.sindex = self['menu'].getIndex()
			if self.mounted:
				mp = self.mountpoints.get(self.disk[0], self.sindex+1)
				rmp = self.mountpoints.getRealMount(self.disk[0], self.sindex+1)
				if len(mp) > 0:
					if self.mountpoints.isMounted(mp):
						if self.mountpoints.umount(mp):
							self.mountpoints.delete(mp)
							self.mountpoints.write()
						else:
							msg = _("Unmounting current drive failed! ")
							msg += _("A recording in progress, timeshift or some external tools (like samba, swapfile and nfsd) may cause this problem. ")
							msg += _("Please stop these processes or applications and try again.")
							self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)
					else:
						self.mountpoints.delete(mp)
						self.mountpoints.write()
				elif len(rmp) > 0:
					self.mountpoints.umount(rmp)
				self.refreshMP()
			else:
				self.session.openWithCallback(self.refreshMP, HddMountDevice, self.disk[0], self.sindex + 1)
