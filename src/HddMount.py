# for localized messages
from . import _

from enigma import *
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Tools.Directories import fileExists, crawlDirectory, resolveFilename, SCOPE_CURRENT_PLUGIN
from Tools.LoadPixmap import LoadPixmap
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Button import Button
from Components.Label import Label
from Components.Sources.List import List
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop

from MountPoints import MountPoints
from Disks import Disks
from ExtraMessageBox import ExtraMessageBox

import os
import re

class HddMountDevice(Screen):

	skin = """
		<screen name="HddMountDevice" position="center,center" size="560,430" title="Hard Drive Mount">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget name="menu" position="20,45" scrollbarMode="showOnDemand" size="520,380" transparent="1" />
		</screen>"""

	def __init__(self, session, device, partition):
		Screen.__init__(self, session)
		self.setTitle(_("Mount points"))

		self.device = device
		self.partition = partition
		self.mountpoints = MountPoints()
		self.mountpoints.read()
		self.fast = False

		self.list = []
		self.list.append(_("Mount as main hdd"))
		self.list.append(_("Mount as %s") % ("/media/hdd1"))
		self.list.append(_("Mount as %s") % ("/media/hdd2"))
		self.list.append(_("Mount as %s") % ("/media/hdd3"))
		self.list.append(_("Mount as %s") % ("/media/hdd4"))
		self.list.append(_("Mount as %s") % ("/media/hdd5"))
		self.list.append(_("Mount as %s") % ("/media/usb"))
		self.list.append(_("Mount as %s") % ("/media/usb1"))
		self.list.append(_("Mount as %s") % ("/media/usb2"))
		self.list.append(_("Mount as %s") % ("/media/usb3"))
		self.list.append(_("Mount as %s") % ("/media/usb4"))
		self.list.append(_("Mount as %s") % ("/media/usb5"))
		self.list.append(_("Mount on custom path"))

		self["menu"] = MenuList(self.list)

		self["key_red"] = Button(_("Fixed mount"))
		self["key_green"] = Button(_("Fast mount"))
		self["key_blue"] = Button(_("Exit"))
		self["key_yellow"] = Button("")
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"blue": self.close,
			"green": self.green,
			"red": self.ok,
			"cancel": self.close,
		}, -2)

	def ok(self):
		self.fast = False
		selected = self["menu"].getSelectedIndex()
		if selected == 0:
			self.setMountPoint("/media/hdd")
		elif selected == 1:
			self.setMountPoint("/media/hdd1")
		elif selected == 2:
			self.setMountPoint("/media/hdd2")
		elif selected == 3:
			self.setMountPoint("/media/hdd3")
		elif selected == 4:
			self.setMountPoint("/media/hdd4")
		elif selected == 5:
			self.setMountPoint("/media/hdd5")
		elif selected == 6:
			self.setMountPoint("/media/usb")
		elif selected == 7:
			self.setMountPoint("/media/usb1")
		elif selected == 8:
			self.setMountPoint("/media/usb2")
		elif selected == 9:
			self.setMountPoint("/media/usb3")
		elif selected == 10:
			self.setMountPoint("/media/usb4")
		elif selected == 11:
			self.setMountPoint("/media/usb5")
		elif selected == 12:
			self.session.openWithCallback(self.customPath, VirtualKeyBoard, title=_("Insert mount point:"), text="/media/custom")

	def green(self):
		self.fast = True
		selected = self["menu"].getSelectedIndex()
		if selected == 0:
			self.setMountPoint("/media/hdd")
		elif selected == 1:
			self.setMountPoint("/media/hdd1")
		elif selected == 2:
			self.setMountPoint("/media/hdd2")
		elif selected == 3:
			self.setMountPoint("/media/hdd3")
		elif selected == 4:
			self.setMountPoint("/media/hdd4")
		elif selected == 5:
			self.setMountPoint("/media/hdd5")
		elif selected == 6:
			self.setMountPoint("/media/usb")
		elif selected == 7:
			self.setMountPoint("/media/usb1")
		elif selected == 8:
			self.setMountPoint("/media/usb2")
		elif selected == 9:
			self.setMountPoint("/media/usb3")
		elif selected == 10:
			self.setMountPoint("/media/usb4")
		elif selected == 11:
			self.setMountPoint("/media/usb5")
		elif selected == 12:
			self.session.openWithCallback(self.customPath, VirtualKeyBoard, title=_("Insert mount point:"), text="/media/custom")

	def customPath(self, result):
		if result and len(result) > 0:
			result = result.rstrip("/")
			os.system("mkdir -p %s" % result)
			self.setMountPoint(result)

	def setMountPoint(self, path):
		self.cpath = path
		if self.mountpoints.exist(path):
			self.session.openWithCallback(self.setMountPointCb, ExtraMessageBox, _("Selected mount point is already used by another drive."), _("Mount point exist!"),
																[ [ _("Change old drive with this new drive"), "ok.png" ],
																[ _("Keep old drive"), "cancel.png" ],
																])
		else:
			self.setMountPointCb(0)

	def setMountPointCb(self, result):
		if result == 0:
			if self.mountpoints.isMounted(self.cpath):
				if not self.mountpoints.umount(self.cpath):
					msg = _("Unmounting current drive failed! ")
					msg += _("A recording in progress, timeshift or some external tools (like samba, swapfile and nfsd) may cause this problem. ")
					msg += _("Please stop these processes or applications and try again.")
					self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)
					self.close()
					return
			self.mountpoints.delete(self.cpath)
			if not self.fast:
				self.mountpoints.add(self.device, self.partition, self.cpath)
			self.mountpoints.write()
			if not self.mountpoints.mount(self.device, self.partition, self.cpath):
				msg = _("Mounting new drive failed! ")
				msg += _("Please check the filesystem or format it and try again.")
				self.session.open(MessageBox, msg, MessageBox.TYPE_ERROR)
			elif self.cpath == "/media/hdd":
				os.system("mkdir -p /media/hdd/movie")

			if not self.fast:
				msg = _("Changing fixed mounted drive requires a system restart in order to take effect. ")
				msg += _("Do you want to restart your receiver now?")
				self.session.openWithCallback(self.restartBox, MessageBox, msg, MessageBox.TYPE_YESNO, title=_("Restart receiver"))
			else:
				self.close()

	def restartBox(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 2)
		else:
			self.close()

def MountEntry(description, details):
	picture = LoadPixmap(cached = True, path = resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/DeviceManager/icons/diskusb.png"));
	return (picture, description, details)

class HddFastRemove(Screen):

	skin = """
		<screen name="HddFastRemove" position="center,center" size="560,430" title="Hard Drive Fast Umount">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="140,0" size="140,40" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_blue" position="140,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget source="menu" render="Listbox" position="10,55" size="520,380" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
						MultiContentEntryPixmapAlphaTest(pos = (5, 0), size = (48, 48), png = 0),
						MultiContentEntryText(pos = (65, 3), size = (190, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),
						MultiContentEntryText(pos = (165, 27), size = (290, 38), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 2),
						],
						"fonts": [gFont("Regular", 22), gFont("Regular", 18)],
						"itemHeight": 50
					}
				</convert>
			</widget>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Fast Mounted Remove"))
		self.refreshMP(False)

		self["menu"] = List(self.disks)
		self["key_red"] = Button(_("Unmount"))
		self["key_blue"] = Button(_("Exit"))
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"blue": self.close,
			"red": self.red,
			"cancel": self.close,
		}, -2)

	def red(self):
		if len(self.mounts) > 0:
			self.sindex = self["menu"].getIndex()
			self.mountpoints.umount(self.mounts[self.sindex]) # actually umount device here - also check both cases possible - for instance error case also check with stay in /e.g. /media/usb folder on telnet
			msg = _("Fast mounted media unmounted successfully. ")
			msg += _("You can safely remove the device now, if there are no other mounted partitions from it. ")
			msg += _("Please unmount fixed mounted devices with 'Storage device manager' panel.")
			self.session.open(MessageBox, msg, MessageBox.TYPE_INFO)
			self.refreshMP(True)

	def refreshMP(self, uirefresh=True):
		self.mdisks = Disks()
		self.mountpoints = MountPoints()
		self.mountpoints.read()
		self.disks = list()
		self.mounts = list()
		for disk in self.mdisks.disks:
			if disk[2] and not disk[7]:
				diskname = disk[3]
				for partition in disk[5]:
					mp = ""
					rmp = ""
					try:
						mp = self.mountpoints.get(partition[0][:3], int(partition[0][3:]))
						rmp = self.mountpoints.getRealMount(partition[0][:3], int(partition[0][3:]))
					except Exception, e:
						pass
					if len(mp) > 0:
						self.disks.append(MountEntry(disk[3], _("P.%s (Fixed: %s)") % (partition[0][3:], mp)))
						self.mounts.append(mp)
					elif len(rmp) > 0:
						self.disks.append(MountEntry(disk[3], _("P.%s (Fast: %s)") % (partition[0][3:], rmp)))
						self.mounts.append(rmp)
		if uirefresh:
			self["menu"].setList(self.disks)
