from enigma import eTimer
from Screens.Screen import Screen
from Components.Label import Label

class ExtraActionBox(Screen):

	skin = """
		<screen name="ExtraActionBox" position="center,center" size="560,70">
			<widget name="message" position="10,10" size="538,48" font="Regular;20" halign="center" valign="center" />
		</screen>"""

	def __init__(self, session, message, title, action):
		Screen.__init__(self, session)
		self.ctitle = title
		self.caction = action

		self["message"] = Label(message)
		self.timer = eTimer()
		self.timer.callback.append(self.__setTitle)
		self.timer.start(500, 1)

	def __setTitle(self):
		self.setTitle(self.ctitle)
		self.timer = eTimer()
		self.timer.callback.append(self.__start)
		self.timer.start(500, 1)

	def __start(self):
		self.close(self.caction())
