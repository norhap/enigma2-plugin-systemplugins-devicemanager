# for localized messages
from . import _

from HddSetup import HddSetup
from HddMount import HddFastRemove
from Plugins.Plugin import PluginDescriptor
import os

def supportExtFat():
	if "exfat-fuse" in open("/etc/filesystems").read():
		pass
	else:
		os.system("echo exfat-fuse >> /etc/filesystems")

def deviceManagerMain(session, **kwargs):
	supportExtFat()
	session.open(HddSetup)

def deviceManagerSetup(menuid, **kwargs):
	if menuid != "system":
		return []
	return [(_("Storage device manager"), deviceManagerMain, "device_manager", None)]

def deviceManagerFastRemove(session, **kwargs):
	session.open(HddFastRemove)


def Plugins(**kwargs):
	return [PluginDescriptor(name=_("Storage device manager"), description=_("Format and partition storage devices and manage mount points"), where=PluginDescriptor.WHERE_MENU, fnc=deviceManagerSetup),
			PluginDescriptor(name=_("Fast mounted drives removal"), description=_("Quickly and safely remove storage devices"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=deviceManagerFastRemove)]
