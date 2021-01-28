import boxbranding
try:
	import urllib2
except ImportError:
	import urllib

from enigma import eConsoleAppContainer, eDVBResourceManager, eGetEnigmaDebugLvl, eLabel, eTimer, getBoxBrand, getBoxType, getDesktop, getE2Rev
from os import listdir, popen, remove
from os.path import getmtime, isfile, join as pathjoin
from six import PY2, PY3, ensure_str as ensurestr, text_type as texttype

from skin import parameters
from Components.About import about
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.Console import Console
from Components.GUIComponent import GUIComponent
from Components.Harddisk import Harddisk, harddiskmanager
from Components.Label import Label
from Components.Network import iNetwork
from Components.NimManager import nimmanager
from Components.Pixmap import MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.SystemInfo import SystemInfo
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists, pathExists
from Tools.Geolocation import geolocation
from Tools.StbHardware import getFPVersion, getBoxProc, getBoxProcType, getHWSerial, getBoxRCType


class About(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("About Information"))
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		hddsplit = parameters.get("AboutHddSplit", 0)

		model = getBoxType()

		try:
			procmodel = getBoxProc()
		except Exception as err:
			procmodel = boxbranding.getMachineProcModel()

		stbplatform = boxbranding.getMachineBuild()

		AboutText = _("Hardware: ") + model + "\n"
		if stbplatform != model:
			AboutText += _("Platform: ") + stbplatform + "\n"
		if procmodel != model:
			AboutText += _("Proc model: ") + procmodel + "\n"

		procmodeltype = getBoxProcType()
		if procmodeltype is not None and procmodeltype != "unknown":
			AboutText += _("Hardware type: ") + procmodeltype + "\n"

		hwserial = getHWSerial()
		if hwserial is not None and hwserial != "unknown":
			AboutText += _("Hardware serial: ") + hwserial + "\n"
		if hwserial is not None and hwserial == "unknown":
			AboutText += _("Hardware serial: ") + about.getCPUSerial() + "\n"

		if fileExists("/proc/stb/info/release"):
			hwrelease = open("/proc/stb/info/release", "r").read().strip()
			AboutText += _("Factory release: ") + hwrelease + "\n"

		AboutText += _("Brand/Meta: ") + getBoxBrand() + "\n"

		AboutText += "\n"
		cpu = about.getCPUInfoString()
		AboutText += _("CPU: ") + cpu + "\n"
		AboutText += _("CPU brand: ") + about.getCPUBrand() + "\n"

		socfamily = boxbranding.getSoCFamily()
		if socfamily is not None:
			AboutText += _("SoC family: ") + socfamily + "\n"

		AboutText += _("CPU architecture: ") + about.getCPUArch() + "\n"

		AboutText += "\n"
		if fileExists("/proc/sys/kernel/random/boot_id"):
			bootid = open("/proc/sys/kernel/random/boot_id", "r").read().strip()
			AboutText += _("Boot ID: ") + bootid + "\n"
		if fileExists("/proc/sys/kernel/random/uuid"):
			uuid = open("/proc/sys/kernel/random/uuid", "r").read().strip()
			AboutText += _("UUID: ") + uuid + "\n"

		if not boxbranding.getDisplayType().startswith(' '):
			AboutText += "\n"
			AboutText += _("Display type: ") + boxbranding.getDisplayType() + "\n"

		# [WanWizard] Removed until we find a reliable way to determine the installation date
		# AboutText += _("Installed: ") + about.getFlashDateString() + "\n"

		EnigmaVersion = about.getEnigmaVersionString()
		EnigmaVersion = EnigmaVersion.rsplit("-", EnigmaVersion.count("-") - 2)
		if len(EnigmaVersion) == 3:
			EnigmaVersion = EnigmaVersion[0] + " (" + EnigmaVersion[2] + "-" + EnigmaVersion[1] + ")"
		else:
			EnigmaVersion = EnigmaVersion[0] + " (" + EnigmaVersion[1] + ")"
		EnigmaVersion = _("Enigma2 version: ") + EnigmaVersion
		self["EnigmaVersion"] = StaticText(EnigmaVersion)
		AboutText += "\n" + EnigmaVersion + "\n"
		AboutText += _("Enigma2 revision: ") + getE2Rev() + "\n"
		AboutText += _("Last update: ") + about.getUpdateDateString() + "\n"
		AboutText += _("Enigma2 (re)starts: %d\n") % config.misc.startCounter.value
		AboutText += _("Enigma2 debug level: %d\n") % eGetEnigmaDebugLvl()

		if fileExists("/etc/openvision/mediaservice"):
			mediaservice = open("/etc/openvision/mediaservice", "r").read().strip()
			AboutText += _("Media service: ") + mediaservice.replace("enigma2-plugin-systemplugins-", "") + "\n"

		AboutText += "\n"

		AboutText += _("Drivers version: ") + about.getDriverInstalledDate() + "\n"
		AboutText += _("Kernel version: ") + boxbranding.getKernelVersion() + "\n"

		modulelayout = popen('find /lib/modules/ -type f -name "openvision.ko" -exec modprobe --dump-modversions {} \; | grep "module_layout" | cut -c-11').read().strip()
		if modulelayout is not None and modulelayout != "":
			AboutText += _("Kernel module layout: ") + modulelayout + "\n"
		else:
			AboutText += _("Kernel module layout: ") + _("N/A") + "\n"

		GStreamerVersion = _("GStreamer version: ") + about.getGStreamerVersionString(cpu).replace("GStreamer", "")
		self["GStreamerVersion"] = StaticText(GStreamerVersion)
		AboutText += "\n" + GStreamerVersion + "\n"

		FFmpegVersion = _("FFmpeg version: ") + about.getFFmpegVersionString()
		self["FFmpegVersion"] = StaticText(FFmpegVersion)
		AboutText += FFmpegVersion + "\n"

		AboutText += "\n"
		AboutText += _("Python version: ") + about.getPythonVersionString() + "\n"
		AboutText += "\n"

		fp_version = getFPVersion()
		if fp_version is None or fp_version == "unknown":
			fp_version = ""
		else:
			fp_version = _("Front processor version: %s") % fp_version

			AboutText += fp_version + "\n"

		self["FPVersion"] = StaticText(fp_version)

		AboutText += _('Skin & Resolution: %s (%sx%s)\n') % (config.skin.primary_skin.value.split('/')[0], getDesktop(0).size().width(), getDesktop(0).size().height())

		self["TunerHeader"] = StaticText(_("Detected NIMs:"))
		AboutText += "\n"
		AboutText += _("Detected NIMs:") + "\n"

		nims = nimmanager.nimListCompressed()
		for count in range(len(nims)):
			if count < 4:
				self["Tuner" + str(count)] = StaticText(nims[count])
			else:
				self["Tuner" + str(count)] = StaticText("")
			AboutText += nims[count] + "\n"

		self["HDDHeader"] = StaticText(_("Detected HDD:"))
		AboutText += "\n"
		AboutText += _("Detected HDD:") + "\n"

		hddlist = harddiskmanager.HDDList()
		hddinfo = ""
		if hddlist:
			formatstring = hddsplit and "%s:%s, %.1f %sB %s" or "%s\n(%s, %.1f %sB %s)"
			for count in range(len(hddlist)):
				if hddinfo:
					hddinfo += "\n"
				hdd = hddlist[count][1]
				if int(hdd.free()) > 1024:
					hddinfo += formatstring % (hdd.model(), hdd.capacity(), hdd.Totalfree() / 1024.0, "G", _("free"))
				else:
					hddinfo += formatstring % (hdd.model(), hdd.capacity(), hdd.Totalfree(), "M", _("free"))
		else:
			hddinfo = _("none")
		self["hddA"] = StaticText(hddinfo)
		AboutText += hddinfo + "\n\n" + _("Network Info:")
		for x in about.GetIPsFromNetworkInterfaces():
			AboutText += "\n" + x[0] + ": " + x[1]
		AboutText += '\n\n' + _("Uptime") + ": " + about.getBoxUptime()

		self["AboutScrollLabel"] = ScrollLabel(AboutText)
		self["key_green"] = Button(_("Translations"))
		self["key_red"] = Button(_("Latest Commits"))
		self["key_yellow"] = Button(_("Troubleshoot"))
		self["key_blue"] = Button(_("Memory Info"))

		self["actions"] = ActionMap(["ColorActions", "SetupActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"red": self.showCommits,
			"green": self.showTranslationInfo,
			"blue": self.showMemoryInfo,
			"yellow": self.showTroubleshoot,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown
		})

	def showTranslationInfo(self):
		self.session.open(TranslationInfo)

	def showCommits(self):
		self.session.open(CommitInfo)

	def showMemoryInfo(self):
		self.session.open(MemoryInfo)

	def showTroubleshoot(self):
		self.session.open(Troubleshoot)

class OpenVisionInformation(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Open Vision Information"))
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		OpenVisionInformationText = _("Open Vision information") + "\n"

		OpenVisionInformationText += "\n"

		OpenVisionInformationText += _("Donate: ") + "https://forum.openvision.tech/app.php/donate" + "\n"

		OpenVisionInformationText += "\n"

		if config.misc.OVupdatecheck.value is True:
			try:
				if boxbranding.getVisionVersion().startswith("10"):
					ovurl = "https://raw.githubusercontent.com/OpenVisionE2/openvision-development-platform/develop/meta-openvision/conf/distro/revision.conf"
				else:
					ovurl = "https://raw.githubusercontent.com/OpenVisionE2/openvision-oe/develop/meta-openvision/conf/distro/revision.conf"
				if PY2:
					ovresponse = urllib2.urlopen(ovurl)
					ovrevision = ovresponse.read()
					ovrevisionupdate = int(filter(str.isdigit, ovrevision))
				else:
					ovresponse = urllib.request.urlopen(ovurl)
					ovrevision = ovresponse.read().decode()
					ovrevisionupdate = ovrevision.split('r')[1][:3]
			except Exception as err:
				ovrevisionupdate = _("Requires internet connection")
		else:
			ovrevisionupdate = _("Disabled in configuration")

		if fileExists("/etc/openvision/visionversion"):
			visionversion = open("/etc/openvision/visionversion", "r").read().strip()
			OpenVisionInformationText += _("Open Vision version: ") + visionversion + "\n"
		else:
			OpenVisionInformationText += _("Open Vision version: ") + boxbranding.getVisionVersion() + "\n"

		if fileExists("/etc/openvision/visionrevision"):
			visionrevision = open("/etc/openvision/visionrevision", "r").read().strip()
			OpenVisionInformationText += _("Open Vision revision: ") + visionrevision + " " + _("(Latest revision on github: ") + str(ovrevisionupdate) + ")" + "\n"
		else:
			OpenVisionInformationText += _("Open Vision revision: ") + boxbranding.getVisionRevision() + " " + _("(Latest revision on github: ") + str(ovrevisionupdate) + ")" + "\n"

		if fileExists("/etc/openvision/visionlanguage"):
			visionlanguage = open("/etc/openvision/visionlanguage", "r").read().strip()
			OpenVisionInformationText += _("Open Vision language: ") + visionlanguage + "\n"

		OpenVisionInformationText += _("Open Vision module: ") + about.getVisionModule() + "\n"

		if fileExists("/etc/openvision/multiboot"):
			multibootflag = open("/etc/openvision/multiboot", "r").read().strip()
			if multibootflag == "1":
				OpenVisionInformationText += _("Soft multiboot: ") + _("Yes") + "\n"
			else:
				OpenVisionInformationText += _("Soft multiboot: ") + _("No") + "\n"
		else:
			OpenVisionInformationText += _("Soft multiboot: ") + _("Yes") + "\n"

		OpenVisionInformationText += _("Flash type: ") + about.getFlashType() + "\n"

		OpenVisionInformationText += "\n"

		boxrctype = getBoxRCType()
		if boxrctype is not None and boxrctype != "unknown":
			OpenVisionInformationText += _("Factory RC type: ") + boxrctype + "\n"
		if boxrctype is not None and boxrctype == "unknown":
			if fileExists("/usr/bin/remotecfg"):
				OpenVisionInformationText += _("RC type: ") + _("Amlogic remote") + "\n"
			elif fileExists("/usr/sbin/lircd"):
				OpenVisionInformationText += _("RC type: ") + _("LIRC remote") + "\n"

		OpenVisionInformationText += _("Open Vision RC type: ") + boxbranding.getRCType() + "\n"
		OpenVisionInformationText += _("Open Vision RC name: ") + boxbranding.getRCName() + "\n"
		OpenVisionInformationText += _("Open Vision RC ID number: ") + boxbranding.getRCIDNum() + "\n"

		OpenVisionInformationText += "\n"

		if SystemInfo["HiSilicon"]:
			OpenVisionInformationText += _("HiSilicon dedicated information") + "\n"

			grab = popen("opkg list-installed | grep -- -grab | cut -f4 -d'-'").read().strip()
			if grab != "" and grab != "r0":
				OpenVisionInformationText += _("Grab: ") + grab + "\n"

			hihalt = popen("opkg list-installed | grep -- -hihalt | cut -f4 -d'-'").read().strip()
			if hihalt != "":
				OpenVisionInformationText += _("Halt: ") + hihalt + "\n"

			libs = popen("opkg list-installed | grep -- -libs | cut -f4 -d'-'").read().strip()
			if libs != "":
				OpenVisionInformationText += _("Libs: ") + libs + "\n"

			partitions = popen("opkg list-installed | grep -- -partitions | cut -f4 -d'-'").read().strip()
			if partitions != "":
				OpenVisionInformationText += _("Partitions: ") + partitions + "\n"

			reader = popen("opkg list-installed | grep -- -reader | cut -f4 -d'-'").read().strip()
			if reader != "":
				OpenVisionInformationText += _("Reader: ") + reader + "\n"

			showiframe = popen("opkg list-installed | grep -- -showiframe | cut -f4 -d'-'").read().strip()
			if showiframe != "":
				OpenVisionInformationText += _("Showiframe: ") + showiframe + "\n"

			OpenVisionInformationText += "\n"

		OpenVisionInformationText += _("Image architecture: ") + boxbranding.getImageArch() + "\n"
		if boxbranding.getImageFolder() != "":
			OpenVisionInformationText += _("Image folder: ") + boxbranding.getImageFolder() + "\n"
		if boxbranding.getImageFileSystem() != "":
			OpenVisionInformationText += _("Image file system: ") + boxbranding.getImageFileSystem() + "\n"
		OpenVisionInformationText += _("Image: ") + boxbranding.getImageDistro() + "\n"
		OpenVisionInformationText += _("Feed URL: ") + boxbranding.getFeedsUrl() + "\n"

		OpenVisionInformationText += _("Compiled by: ") + boxbranding.getDeveloperName() + "\n"
		OpenVisionInformationText += _("Build date: ") + about.getBuildDateString() + "\n"

		OpenVisionInformationText += _("OE: ") + boxbranding.getImageBuild() + "\n"

		OpenVisionInformationText += "\n"

		if boxbranding.getImageFPU() != "":
			OpenVisionInformationText += _("FPU: ") + boxbranding.getImageFPU() + "\n"

		if boxbranding.getImageArch() == "aarch64":
			if boxbranding.getHaveMultiLib() == "True":
				OpenVisionInformationText += _("MultiLib: ") + _("Yes") + "\n"
			else:
				OpenVisionInformationText += _("MultiLib: ") + _("No") + "\n"

		OpenVisionInformationText += "\n"

		if boxbranding.getMachineMtdBoot() != "":
			OpenVisionInformationText += _("MTD boot: ") + boxbranding.getMachineMtdBoot() + "\n"
		if boxbranding.getMachineMtdRoot() != "":
			OpenVisionInformationText += _("MTD root: ") + boxbranding.getMachineMtdRoot() + "\n"
		if boxbranding.getMachineMtdKernel() != "":
			OpenVisionInformationText += _("MTD kernel: ") + boxbranding.getMachineMtdKernel() + "\n"

		if boxbranding.getMachineRootFile() != "":
			OpenVisionInformationText += _("Root file: ") + boxbranding.getMachineRootFile() + "\n"
		if boxbranding.getMachineKernelFile() != "":
			OpenVisionInformationText += _("Kernel file: ") + boxbranding.getMachineKernelFile() + "\n"

		if boxbranding.getMachineMKUBIFS() != "":
			OpenVisionInformationText += _("MKUBIFS: ") + boxbranding.getMachineMKUBIFS() + "\n"
		if boxbranding.getMachineUBINIZE() != "":
			OpenVisionInformationText += _("UBINIZE: ") + boxbranding.getMachineUBINIZE() + "\n"

		OpenVisionInformationText += "\n"

		if fileExists("/proc/device-tree/amlogic-dt-id"):
			devicetid = open("/proc/device-tree/amlogic-dt-id", "r").read().strip()
			OpenVisionInformationText += _("Device id: ") + devicetid + "\n"

		if fileExists("/proc/device-tree/le-dt-id"):
			giventid = open("/proc/device-tree/le-dt-id", "r").read().strip()
			OpenVisionInformationText += _("Given device id: ") + giventid + "\n"

		self["AboutScrollLabel"] = ScrollLabel(OpenVisionInformationText)
		self["key_red"] = Button(_("Close"))

		self["actions"] = ActionMap(["ColorActions", "SetupActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown
		})

class DVBInformation(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("DVB Information"))
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		DVBInformationText = _("DVB information") + "\n"

		DVBInformationText += "\n"

		DVBInformationText += _("DVB API: ") + about.getDVBAPI() + "\n"

		numSlots = 0
		dvbfetooltxt = ""
		nimSlots = nimmanager.getSlotCount()
		for nim in range(nimSlots):
			dvbfetooltxt += eDVBResourceManager.getInstance().getFrontendCapabilities(nim)

		dvbapiversion = ""
		dvbapiversion = dvbfetooltxt.splitlines()[0].replace("DVB API version: ", "").strip()
		DVBInformationText += _("DVB API version: ") + dvbapiversion + "\n"

		DVBInformationText += "\n"

		if boxbranding.getHaveTranscoding() == "True":
			DVBInformationText += _("Transcoding: ") + _("Yes") + "\n"
		else:
			DVBInformationText += _("Transcoding: ") + _("No") + "\n"

		if boxbranding.getHaveMultiTranscoding() == "True":
			DVBInformationText += _("MultiTranscoding: ") + _("Yes") + "\n"
		else:
			DVBInformationText += _("MultiTranscoding: ") + _("No") + "\n"

		DVBInformationText += "\n"

		if "DVBC" in dvbfetooltxt or "DVB-C" in dvbfetooltxt:
			DVBInformationText += _("DVB-C: ") + _("Yes") + "\n"
		else:
			DVBInformationText += _("DVB-C: ") + _("No") + "\n"
		if "DVBS" in dvbfetooltxt or "DVB-S" in dvbfetooltxt:
			DVBInformationText += _("DVB-S: ") + _("Yes") + "\n"
		else:
			DVBInformationText += _("DVB-S: ") + _("No") + "\n"
		if "DVBT" in dvbfetooltxt or "DVB-T" in dvbfetooltxt:
			DVBInformationText += _("DVB-T: ") + _("Yes") + "\n"
		else:
			DVBInformationText += _("DVB-T: ") + _("No") + "\n"

		DVBInformationText += "\n"

		if "MULTISTREAM" in dvbfetooltxt:
			DVBInformationText += _("Multistream: ") + _("Yes") + "\n"
		else:
			DVBInformationText += _("Multistream: ") + _("No") + "\n"

		DVBInformationText += "\n"

		if "ANNEX_A" in dvbfetooltxt or "ANNEX-A" in dvbfetooltxt:
			DVBInformationText += _("ANNEX-A: ") + _("Yes") + "\n"
		else:
			DVBInformationText += _("ANNEX-A: ") + _("No") + "\n"
		if "ANNEX_B" in dvbfetooltxt or "ANNEX-B" in dvbfetooltxt:
			DVBInformationText += _("ANNEX-B: ") + _("Yes") + "\n"
		else:
			DVBInformationText += _("ANNEX-B: ") + _("No") + "\n"
		if "ANNEX_C" in dvbfetooltxt or "ANNEX-C" in dvbfetooltxt:
			DVBInformationText += _("ANNEX-C: ") + _("Yes") + "\n"
		else:
			DVBInformationText += _("ANNEX-C: ") + _("No") + "\n"

		self["AboutScrollLabel"] = ScrollLabel(DVBInformationText)
		self["key_red"] = Button(_("Close"))

		self["actions"] = ActionMap(["ColorActions", "SetupActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown
		})

class Geolocation(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Geolocation Information"))
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		GeolocationText = _("Geolocation information") + "\n"

		GeolocationText += "\n"

		try:
			geolocationData = geolocation.getGeolocationData(fields="continent,country,regionName,city,timezone,currency,lat,lon", useCache=True)
			continent = geolocationData.get("continent", None)
			if isinstance(continent, texttype):
				continent = ensurestr(continent.encode(encoding="UTF-8", errors="ignore"))
			if continent is not None:
				GeolocationText += _("Continent: ") + continent + "\n"

			country = geolocationData.get("country", None)
			if isinstance(country, texttype):
				country = ensurestr(country.encode(encoding="UTF-8", errors="ignore"))
			if country is not None:
				GeolocationText += _("Country: ") + country + "\n"

			state = geolocationData.get("regionName", None)
			if isinstance(state, texttype):
				state = ensurestr(state.encode(encoding="UTF-8", errors="ignore"))
			if state is not None:
				GeolocationText += _("State: ") + state + "\n"

			city = geolocationData.get("city", None)
			if isinstance(city, texttype):
				city = ensurestr(city.encode(encoding="UTF-8", errors="ignore"))
			if city is not None:
				GeolocationText += _("City: ") + city + "\n"

			GeolocationText += "\n"

			timezone = geolocationData.get("timezone", None)
			if isinstance(timezone, texttype):
				timezone = ensurestr(timezone.encode(encoding="UTF-8", errors="ignore"))
			if timezone is not None:
				GeolocationText += _("Timezone: ") + timezone + "\n"

			currency = geolocationData.get("currency", None)
			if isinstance(currency, texttype):
				currency = ensurestr(currency.encode(encoding="UTF-8", errors="ignore"))
			if currency is not None:
				GeolocationText += _("Currency: ") + currency + "\n"

			GeolocationText += "\n"

			latitude = geolocationData.get("lat", None)
			if str(float(latitude)) is not None:
				GeolocationText += _("Latitude: ") + str(float(latitude)) + "\n"

			longitude = geolocationData.get("lon", None)
			if str(float(longitude)) is not None:
				GeolocationText += _("Longitude: ") + str(float(longitude)) + "\n"
			self["AboutScrollLabel"] = ScrollLabel(GeolocationText)
		except Exception as err:
			self["AboutScrollLabel"] = ScrollLabel(_("Requires internet connection"))

		self["key_red"] = Button(_("Close"))

		self["actions"] = ActionMap(["ColorActions", "SetupActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown
		})

class BenchmarkInformation(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Benchmark Information"))
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		BenchmarkInformationText = _("Benchmark information") + "\n"

		BenchmarkInformationText += "\n"

		BenchmarkInformationText += _("CPU benchmark: ") + about.getCPUBenchmark() + "\n"

		self["AboutScrollLabel"] = ScrollLabel(BenchmarkInformationText)
		self["key_red"] = Button(_("Close"))

		self["actions"] = ActionMap(["ColorActions", "SetupActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown
		})

class Devices(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Device Information"))
		self["TunerHeader"] = StaticText(_("Detected tuners:"))
		self["HDDHeader"] = StaticText(_("Detected devices:"))
		self["MountsHeader"] = StaticText(_("Network servers:"))
		self["nims"] = StaticText()
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		for count in (0, 1, 2, 3):
			self["Tuner" + str(count)] = StaticText("")
		self["hdd"] = StaticText()
		self["mounts"] = StaticText()
		self.list = []
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.populate2)
		self["key_red"] = Button(_("Close"))
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "TimerEditActions"], {
			"cancel": self.close,
			"ok": self.close,
			"red": self.close
		})
		self.onLayoutFinish.append(self.populate)

	def populate(self):
		self.mountinfo = ''
		self["actions"].setEnabled(False)
		scanning = _("Please wait while scanning for devices...")
		self["nims"].setText(scanning)
		for count in (0, 1, 2, 3):
			self["Tuner" + str(count)].setText(scanning)
		self["hdd"].setText(scanning)
		self['mounts'].setText(scanning)
		self.activityTimer.start(1)

	def populate2(self):
		self.activityTimer.stop()
		self.Console = Console()
		niminfo = ""
		nims = nimmanager.nimListCompressed()
		for count in range(len(nims)):
			if niminfo:
				niminfo += "\n"
			niminfo += nims[count]
		self["nims"].setText(niminfo)

		nims = nimmanager.nimList()
		if len(nims) <= 4:
			for count in (0, 1, 2, 3):
				if count < len(nims):
					self["Tuner" + str(count)].setText(nims[count])
				else:
					self["Tuner" + str(count)].setText("")
		else:
			desc_list = []
			count = 0
			cur_idx = -1
			while count < len(nims):
				data = nims[count].split(":")
				idx = data[0].strip('Tuner').strip()
				desc = data[1].strip()
				if desc_list and desc_list[cur_idx]['desc'] == desc:
					desc_list[cur_idx]['end'] = idx
				else:
					desc_list.append({
						'desc': desc,
						'start': idx,
						'end': idx
					})
					cur_idx += 1
				count += 1

			for count in (0, 1, 2, 3):
				if count < len(desc_list):
					if desc_list[count]['start'] == desc_list[count]['end']:
						text = "Tuner %s: %s" % (desc_list[count]['start'], desc_list[count]['desc'])
					else:
						text = "Tuner %s-%s: %s" % (desc_list[count]['start'], desc_list[count]['end'], desc_list[count]['desc'])
				else:
					text = ""

				self["Tuner" + str(count)].setText(text)

		self.hddlist = harddiskmanager.HDDList()
		self.list = []
		if self.hddlist:
			for count in range(len(self.hddlist)):
				hdd = self.hddlist[count][1]
				hddp = self.hddlist[count][0]
				if "ATA" in hddp:
					hddp = hddp.replace('ATA', '')
					hddp = hddp.replace('Internal', 'ATA Bus ')
				free = hdd.Totalfree()
				if ((float(free) / 1024) / 1024) >= 1:
					freeline = _("Free: ") + str(round(((float(free) / 1024) / 1024), 2)) + _("TB")
				elif (free / 1024) >= 1:
					freeline = _("Free: ") + str(round((float(free) / 1024), 2)) + _("GB")
				elif free >= 1:
					freeline = _("Free: ") + str(free) + _("MB")
				elif "Generic(STORAGE" in hddp:
					continue
				else:
					freeline = _("Free: ") + _("full")
				line = "%s      %s" % (hddp, freeline)
				self.list.append(line)
		self.list = '\n'.join(self.list)
		self["hdd"].setText(self.list)

		self.Console.ePopen("df -mh | grep -v '^Filesystem'", self.Stage1Complete)

	def Stage1Complete(self, result, retval, extra_args=None):
		if PY2:
			result = result.replace('\n                        ', ' ').split('\n')
		else:
			result = result.decode().replace('\n                        ', ' ').split('\n')
		self.mountinfo = ""
		for line in result:
			self.parts = line.split()
			if line and self.parts[0] and (self.parts[0].startswith('192') or self.parts[0].startswith('//192')):
				line = line.split()
				ipaddress = line[0]
				mounttotal = line[1]
				mountfree = line[3]
				if self.mountinfo:
					self.mountinfo += "\n"
				self.mountinfo += "%s (%sB, %sB %s)" % (ipaddress, mounttotal, mountfree, _("free"))
		if pathExists("/media/autofs"):
			for entry in sorted(listdir("/media/autofs")):
				mountEntry = pathjoin("/media/autofs", entry)
				self.mountinfo += _("\n %s " % (mountEntry))

		if self.mountinfo:
			self["mounts"].setText(self.mountinfo)
		else:
			self["mounts"].setText(_('none'))
		self["actions"].setEnabled(True)

class SystemNetworkInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Network Information"))
		self.skinName = ["SystemNetworkInfo", "WlanStatus"]
		self["LabelBSSID"] = StaticText()
		self["LabelESSID"] = StaticText()
		self["LabelQuality"] = StaticText()
		self["LabelSignal"] = StaticText()
		self["LabelBitrate"] = StaticText()
		self["LabelEnc"] = StaticText()
		self["BSSID"] = StaticText()
		self["ESSID"] = StaticText()
		self["quality"] = StaticText()
		self["signal"] = StaticText()
		self["bitrate"] = StaticText()
		self["enc"] = StaticText()
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		self["IFtext"] = StaticText()
		self["IF"] = StaticText()
		self["Statustext"] = StaticText()
		self["statuspic"] = MultiPixmap()
		self["statuspic"].setPixmapNum(1)
		self["statuspic"].show()
		self["devicepic"] = MultiPixmap()

		self["AboutScrollLabel"] = ScrollLabel()

		self.iface = None
		self.createscreen()
		self.iStatus = None

		if iNetwork.isWirelessInterface(self.iface):
			try:
				from Plugins.SystemPlugins.WirelessLan.Wlan import iStatus

				self.iStatus = iStatus
			except ImportError as err:
				pass
			self.resetList()
			self.onClose.append(self.cleanup)

		self["key_red"] = StaticText(_("Close"))

		self["actions"] = ActionMap(["SetupActions", "ColorActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown
		})
		self.onLayoutFinish.append(self.updateStatusbar)

	def createscreen(self):
		self.AboutText = ""
		self.iface = "eth0"
		eth0 = about.getIfConfig('eth0')
		if 'addr' in eth0:
			self.AboutText += _("IP:") + "\t" + eth0['addr'] + "\n"
			if 'netmask' in eth0:
				self.AboutText += _("Netmask:") + "\t" + eth0['netmask'] + "\n"
			if 'hwaddr' in eth0:
				self.AboutText += _("MAC:") + "\t" + eth0['hwaddr'] + "\n"
			self.iface = 'eth0'

		eth1 = about.getIfConfig('eth1')
		if 'addr' in eth1:
			self.AboutText += _("IP:") + "\t" + eth1['addr'] + "\n"
			if 'netmask' in eth1:
				self.AboutText += _("Netmask:") + "\t" + eth1['netmask'] + "\n"
			if 'hwaddr' in eth1:
				self.AboutText += _("MAC:") + "\t" + eth1['hwaddr'] + "\n"
			self.iface = 'eth1'

		ra0 = about.getIfConfig('ra0')
		if 'addr' in ra0:
			self.AboutText += _("IP:") + "\t" + ra0['addr'] + "\n"
			if 'netmask' in ra0:
				self.AboutText += _("Netmask:") + "\t" + ra0['netmask'] + "\n"
			if 'hwaddr' in ra0:
				self.AboutText += _("MAC:") + "\t" + ra0['hwaddr'] + "\n"
			self.iface = 'ra0'

		wlan0 = about.getIfConfig('wlan0')
		if 'addr' in wlan0:
			self.AboutText += _("IP:") + "\t" + wlan0['addr'] + "\n"
			if 'netmask' in wlan0:
				self.AboutText += _("Netmask:") + "\t" + wlan0['netmask'] + "\n"
			if 'hwaddr' in wlan0:
				self.AboutText += _("MAC:") + "\t" + wlan0['hwaddr'] + "\n"
			self.iface = 'wlan0'

		wlan3 = about.getIfConfig('wlan3')
		if 'addr' in wlan3:
			self.AboutText += _("IP:") + "\t" + wlan3['addr'] + "\n"
			if 'netmask' in wlan3:
				self.AboutText += _("Netmask:") + "\t" + wlan3['netmask'] + "\n"
			if 'hwaddr' in wlan3:
				self.AboutText += _("MAC:") + "\t" + wlan3['hwaddr'] + "\n"
			self.iface = 'wlan3'

		rx_bytes, tx_bytes = about.getIfTransferredData(self.iface)
		self.AboutText += "\n"
		self.AboutText += _("Bytes received:") + "\t" + rx_bytes + "\n"
		self.AboutText += _("Bytes sent:") + "\t" + tx_bytes + "\n"

		geolocationData = geolocation.getGeolocationData(fields="isp,org,mobile,proxy,query", useCache=True)
		isp = geolocationData.get("isp", None)
		isporg = geolocationData.get("org", None)
		if isinstance(isp, texttype):
			isp = ensurestr(isp.encode(encoding="UTF-8", errors="ignore"))
		if isinstance(isporg, texttype):
			isporg = ensurestr(isporg.encode(encoding="UTF-8", errors="ignore"))
		self.AboutText += "\n"
		if isp is not None:
			if isporg is not None:
				self.AboutText += _("ISP: ") + isp + " " + "(" + isporg + ")" + "\n"
			else:
				self.AboutText += _("ISP: ") + isp + "\n"

		mobile = geolocationData.get("mobile", False)
		if mobile is not False:
			self.AboutText += _("Mobile: ") + _("Yes") + "\n"
		else:
			self.AboutText += _("Mobile: ") + _("No") + "\n"

		proxy = geolocationData.get("proxy", False)
		if proxy is not False:
			self.AboutText += _("Proxy: ") + _("Yes") + "\n"
		else:
			self.AboutText += _("Proxy: ") + _("No") + "\n"

		publicip = geolocationData.get("query", None)
		if str(publicip) != "":
			self.AboutText += _("Public IP: ") + str(publicip) + "\n"

		self.AboutText += "\n"

		self.console = Console()
		self.console.ePopen('ethtool %s' % self.iface, self.SpeedFinished)

	def SpeedFinished(self, result, retval, extra_args):
		if PY2:
			result_tmp = result.split('\n')
		else:
			result_tmp = result.decode().split('\n')
		for line in result_tmp:
			if 'Speed:' in line:
				speed = line.split(': ')[1][:-4]
				self.AboutText += _("Speed:") + "\t" + speed + _('Mb/s')

		hostname = open('/proc/sys/kernel/hostname').read()
		self.AboutText += "\n"
		self.AboutText += _("Hostname:") + "\t" + hostname + "\n"
		self["AboutScrollLabel"].setText(self.AboutText)

	def cleanup(self):
		if self.iStatus:
			self.iStatus.stopWlanConsole()

	def resetList(self):
		if self.iStatus:
			self.iStatus.getDataForInterface(self.iface, self.getInfoCB)

	def getInfoCB(self, data, status):
		self.LinkState = None
		if data is not None and data:
			if status is not None:
				# getDataForInterface()->iwconfigFinished() in
				# Plugins/SystemPlugins/WirelessLan/Wlan.py sets fields to boolean False
				# if there is no info for them, so we need to check that possibility
				# for each status[self.iface] field...
				if self.iface == 'wlan0' or self.iface == 'wlan3' or self.iface == 'ra0':
					# accesspoint is used in the "enc" code too, so we get it regardless
					if not status[self.iface]["accesspoint"]:
						accesspoint = _("Unknown")
					else:
						if status[self.iface]["accesspoint"] == "Not-Associated":
							accesspoint = _("Not-Associated")
							essid = _("No connection")
						else:
							accesspoint = status[self.iface]["accesspoint"]
					if 'BSSID' in self:
						self.AboutText += _('Accesspoint:') + '\t' + accesspoint + '\n'

					if 'ESSID' in self:
						if not status[self.iface]["essid"]:
							essid = _("Unknown")
						else:
							if status[self.iface]["essid"] == "off":
								essid = _("No connection")
							else:
								essid = status[self.iface]["essid"]
						self.AboutText += _('SSID:') + '\t' + essid + '\n'

					if 'quality' in self:
						if not status[self.iface]["quality"]:
							quality = _("Unknown")
						else:
							quality = status[self.iface]["quality"]
						self.AboutText += _('Link quality:') + '\t' + quality + '\n'

					if 'bitrate' in self:
						if not status[self.iface]["bitrate"]:
							bitrate = _("Unknown")
						else:
							if status[self.iface]["bitrate"] == '0':
								bitrate = _("Unsupported")
							else:
								bitrate = str(status[self.iface]["bitrate"]) + " Mb/s"
						self.AboutText += _('Bitrate:') + '\t' + bitrate + '\n'

					if 'signal' in self:
						if not status[self.iface]["signal"]:
							signal = _("Unknown")
						else:
							signal = status[self.iface]["signal"]
						self.AboutText += _('Signal strength:') + '\t' + signal + '\n'

					if 'enc' in self:
						if not status[self.iface]["encryption"]:
							encryption = _("Unknown")
						else:
							if status[self.iface]["encryption"] == "off":
								if accesspoint == "Not-Associated":
									encryption = _("Disabled")
								else:
									encryption = _("Unsupported")
							else:
								encryption = _("Enabled")
						self.AboutText += _('Encryption:') + '\t' + encryption + '\n'

					if ((status[self.iface]["essid"] and status[self.iface]["essid"] == "off") or not status[self.iface]["accesspoint"] or status[self.iface]["accesspoint"] == "Not-Associated"):
						self.LinkState = False
						self["statuspic"].setPixmapNum(1)
						self["statuspic"].show()
					else:
						self.LinkState = True
						iNetwork.checkNetworkState(self.checkNetworkCB)
					self["AboutScrollLabel"].setText(self.AboutText)

	def exit(self):
		self.close(True)

	def updateStatusbar(self):
		self["IFtext"].setText(_("Network:"))
		self["IF"].setText(iNetwork.getFriendlyAdapterName(self.iface))
		self["Statustext"].setText(_("Link:"))
		if iNetwork.isWirelessInterface(self.iface):
			self["devicepic"].setPixmapNum(1)
			try:
				self.iStatus.getDataForInterface(self.iface, self.getInfoCB)
			except Exception as err:
				self["statuspic"].setPixmapNum(1)
				self["statuspic"].show()
		else:
			iNetwork.getLinkState(self.iface, self.dataAvail)
			self["devicepic"].setPixmapNum(0)
		self["devicepic"].show()

	def dataAvail(self, data):
		if PY3:
			data = data.decode()
		self.LinkState = None
		for line in data.splitlines():
			line = line.strip()
			if 'Link detected:' in line:
				if "yes" in line:
					self.LinkState = True
				else:
					self.LinkState = False
		if self.LinkState:
			iNetwork.checkNetworkState(self.checkNetworkCB)
		else:
			self["statuspic"].setPixmapNum(1)
			self["statuspic"].show()

	def checkNetworkCB(self, data):
		try:
			if iNetwork.getAdapterAttribute(self.iface, "up") is True:
				if self.LinkState is True:
					if data <= 2:
						self["statuspic"].setPixmapNum(0)
					else:
						self["statuspic"].setPixmapNum(1)
				else:
					self["statuspic"].setPixmapNum(1)
			else:
				self["statuspic"].setPixmapNum(1)
			self["statuspic"].show()
		except Exception as err:
			pass

class SystemMemoryInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Memory Information"))
		self.skinName = ["SystemMemoryInfo", "About"]
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		self["AboutScrollLabel"] = ScrollLabel()

		self["key_red"] = Button(_("Close"))
		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
			"cancel": self.close,
			"ok": self.close,
			"red": self.close
		})

		out_lines = open("/proc/meminfo").readlines()
		self.AboutText = _("RAM") + '\n\n'
		RamTotal = "-"
		RamFree = "-"
		for lidx in range(len(out_lines) - 1):
			tstLine = out_lines[lidx].split()
			if "MemTotal:" in tstLine:
				MemTotal = out_lines[lidx].split()
				self.AboutText += _("Total memory:") + "\t" + MemTotal[1] + "\n"
			if "MemFree:" in tstLine:
				MemFree = out_lines[lidx].split()
				self.AboutText += _("Free memory:") + "\t" + MemFree[1] + "\n"
			if "Buffers:" in tstLine:
				Buffers = out_lines[lidx].split()
				self.AboutText += _("Buffers:") + "\t" + Buffers[1] + "\n"
			if "Cached:" in tstLine:
				Cached = out_lines[lidx].split()
				self.AboutText += _("Cached:") + "\t" + Cached[1] + "\n"
			if "SwapTotal:" in tstLine:
				SwapTotal = out_lines[lidx].split()
				self.AboutText += _("Total swap:") + "\t" + SwapTotal[1] + "\n"
			if "SwapFree:" in tstLine:
				SwapFree = out_lines[lidx].split()
				self.AboutText += _("Free swap:") + "\t" + SwapFree[1] + "\n\n"

		self["actions"].setEnabled(False)
		self.Console = Console()
		self.Console.ePopen("df -mh / | grep -v '^Filesystem'", self.Stage1Complete2)

	def Stage1Complete2(self, result, retval, extra_args=None):
		flash = str(result).replace('\n', '')
		flash = flash.split()
		RamTotal = flash[1]
		RamFree = flash[3]

		self.AboutText += _("Flash") + '\n\n'
		self.AboutText += _("Total:") + "\t" + RamTotal + "\n"
		self.AboutText += _("Free:") + "\t" + RamFree + "\n\n"

		self["AboutScrollLabel"].setText(self.AboutText)
		self["actions"].setEnabled(True)

class TranslationInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Translations"))
		# don't remove the string out of the _(), or it can't be "translated" anymore.

		# TRANSLATORS: Add here whatever should be shown in the "translator" about screen, up to 6 lines (use \n for newline)
		info = _("TRANSLATOR_INFO")

		if info == "TRANSLATOR_INFO":
			info = "(N/A)"

		infolines = _("").split("\n")
		infomap = {}
		for x in infolines:
			data = x.split(': ')
			if len(data) != 2:
				continue
			(type, value) = data
			infomap[type] = value
		print("[About] DEBUG: infomap=%s" % str(infomap))

		self["key_red"] = Button(_("Cancel"))
		self["TranslationInfo"] = StaticText(info)
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		translator_name = infomap.get("Language-Team", "none")
		if translator_name == "none":
			translator_name = infomap.get("Last-Translator", "")

		self["TranslatorName"] = StaticText(translator_name)

		self["actions"] = ActionMap(["SetupActions"], {
			"cancel": self.close,
			"ok": self.close
		})

class CommitInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Latest Commits"))
		self.skinName = ["CommitInfo", "About"]
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))
		self["AboutScrollLabel"] = ScrollLabel(_("Please wait"))

		self["actions"] = ActionMap(["SetupActions", "DirectionActions"], {
			"cancel": self.close,
			"ok": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown,
			"left": self.left,
			"right": self.right
		})

		self["key_red"] = Button(_("Cancel"))

		# get the branch to display from the Enigma version
		try:
			branch = "?sha=" + "-".join(about.getEnigmaVersionString().split("-")[3:])
		except Exception as err:
			branch = ""

		if boxbranding.getVisionVersion().startswith("10"):
			oegiturl = "https://api.github.com/repos/OpenVisionE2/openvision-development-platform/commits"
		else:
			oegiturl = "https://api.github.com/repos/OpenVisionE2/openvision-oe/commits"

		self.project = 0
		self.projects = [
			("https://api.github.com/repos/OpenVisionE2/enigma2-openvision/commits" + branch, "Enigma2 - Vision"),
			(oegiturl, "OE - Vision"),
			("https://api.github.com/repos/OpenVisionE2/enigma2-plugins/commits", "Enigma2 plugins"),
			("https://api.github.com/repos/OpenVisionE2/alliance-plugins/commits", "Alliance plugins"),
			("https://api.github.com/repos/OpenVisionE2/OpenWebif/commits", "Open WebIF"),
			("https://api.github.com/repos/OpenVisionE2/openvision-core-plugin/commits", "Vision core plugin"),
			("https://api.github.com/repos/OpenVisionE2/BackupSuite/commits", "Backup Suite plugin"),
			("https://api.github.com/repos/OpenVisionE2/OctEtFHD-skin/commits", "OctEtFHD skin")
		]
		self.cachedProjects = {}
		self.Timer = eTimer()
		self.Timer.callback.append(self.readGithubCommitLogs)
		self.Timer.start(50, True)

	def readGithubCommitLogs(self):
		url = self.projects[self.project][0]
		commitlog = ""
		from datetime import datetime
		from json import loads
		try:
			commitlog += 80 * '-' + '\n'
			commitlog += url.split('/')[-2] + '\n'
			commitlog += 80 * '-' + '\n'
			try:
				# For python 2.7.11 we need to bypass the certificate check
				from ssl import _create_unverified_context
				if PY2:
					log = loads(urllib2.urlopen(url, timeout=5, context=_create_unverified_context()).read())
				else:
					log = loads(urllib.request.urlopen(url, timeout=5, context=_create_unverified_context()).read())
			except Exception as err:
				if PY2:
					log = loads(urllib2.urlopen(url, timeout=5).read())
				else:
					log = loads(urllib.request.urlopen(url, timeout=5).read())
			for c in log:
				creator = c['commit']['author']['name']
				title = c['commit']['message']
				date = datetime.strptime(c['commit']['committer']['date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%x %X')
				commitlog += date + ' ' + creator + '\n' + title + 2 * '\n'
			commitlog = commitlog.encode('utf-8')
			self.cachedProjects[self.projects[self.project][1]] = commitlog
		except Exception as err:
			commitlog += _("Currently the commit log cannot be retrieved - please try later again")
		self["AboutScrollLabel"].setText(commitlog)

	def updateCommitLogs(self):
		if self.projects[self.project][1] in self.cachedProjects:
			self["AboutScrollLabel"].setText(self.cachedProjects[self.projects[self.project][1]])
		else:
			self["AboutScrollLabel"].setText(_("Please wait"))
			self.Timer.start(50, True)

	def left(self):
		self.project = self.project == 0 and len(self.projects) - 1 or self.project - 1
		self.updateCommitLogs()

	def right(self):
		self.project = self.project != len(self.projects) - 1 and self.project + 1 or 0
		self.updateCommitLogs()

class MemoryInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"], {
			"cancel": self.close,
			"ok": self.getMemoryInfo,
			"green": self.getMemoryInfo,
			"blue": self.clearMemory
		})

		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Refresh"))
		self["key_blue"] = Label(_("Clear"))

		self['lmemtext'] = Label()
		self['lmemvalue'] = Label()
		self['rmemtext'] = Label()
		self['rmemvalue'] = Label()

		self['pfree'] = Label()
		self['pused'] = Label()
		self["slide"] = ProgressBar()
		self["slide"].setValue(100)

		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		self["params"] = MemoryInfoSkinParams()

		self['info'] = Label(_("This info is for developers only.\nFor normal users it is not relevant.\nPlease don't panic if you see values displayed looking suspicious!"))

		self.setTitle(_("Memory Info"))
		self.onLayoutFinish.append(self.getMemoryInfo)

	def getMemoryInfo(self):
		try:
			ltext = rtext = ""
			lvalue = rvalue = ""
			mem = 1
			free = 0
			rows_in_column = self["params"].rows_in_column
			for i, line in enumerate(open('/proc/meminfo', 'r')):
				s = line.strip().split(None, 2)
				if len(s) == 3:
					name, size, units = s
				elif len(s) == 2:
					name, size = s
					units = ""
				else:
					continue
				if name.startswith("MemTotal"):
					mem = int(size)
				if name.startswith("MemFree") or name.startswith("Buffers") or name.startswith("Cached"):
					free += int(size)
				if i < rows_in_column:
					ltext += "".join((name, "\n"))
					lvalue += "".join((size, " ", units, "\n"))
				else:
					rtext += "".join((name, "\n"))
					rvalue += "".join((size, " ", units, "\n"))
			self['lmemtext'].setText(ltext)
			self['lmemvalue'].setText(lvalue)
			self['rmemtext'].setText(rtext)
			self['rmemvalue'].setText(rvalue)
			self["slide"].setValue(int(100.0 * (mem - free) / mem + 0.25))
			self['pfree'].setText("%.1f %s" % (100.0 * free / mem, '%'))
			self['pused'].setText("%.1f %s" % (100.0 * (mem - free) / mem, '%'))
		except Exception as err:
			print("[About] getMemoryInfo FAIL: '%s'." % str(err))

	def clearMemory(self):
		eConsoleAppContainer().execute("sync")
		open("/proc/sys/vm/drop_caches", "w").write("3")
		self.getMemoryInfo()

class MemoryInfoSkinParams(GUIComponent):
	def __init__(self):
		GUIComponent.__init__(self)
		self.rows_in_column = 25

	def applySkin(self, desktop, screen):
		if self.skinAttributes is not None:
			attribs = []
			for (attrib, value) in self.skinAttributes:
				if attrib == "rowsincolumn":
					self.rows_in_column = int(value)
			self.skinAttributes = attribs
			applySkin = GUIComponent
		return applySkin()

	GUI_WIDGET = eLabel

class Troubleshoot(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Troubleshoot"))
		self["AboutScrollLabel"] = ScrollLabel(_("Please wait"))
		self["key_red"] = Button()
		self["key_green"] = Button()
		self["lab1"] = StaticText(_("OpenVision"))
		self["lab2"] = StaticText(_("Lets define enigma2 once more"))
		self["lab3"] = StaticText(_("Report problems to:"))
		self["lab4"] = StaticText(_("https://openvision.tech"))
		self["lab5"] = StaticText(_("Sources are available at:"))
		self["lab6"] = StaticText(_("https://github.com/OpenVisionE2"))

		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"], {
			"cancel": self.close,
			"up": self["AboutScrollLabel"].pageUp,
			"down": self["AboutScrollLabel"].pageDown,
			"moveUp": self["AboutScrollLabel"].homePage,
			"moveDown": self["AboutScrollLabel"].endPage,
			"left": self.left,
			"right": self.right,
			"red": self.red,
			"green": self.green
		})

		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.appClosed)
		self.container.dataAvail.append(self.dataAvail)
		self.commandIndex = 0
		self.updateOptions()
		self.onLayoutFinish.append(self.run_console)

	def left(self):
		self.commandIndex = (self.commandIndex - 1) % len(self.commands)
		self.updateKeys()
		self.run_console()

	def right(self):
		self.commandIndex = (self.commandIndex + 1) % len(self.commands)
		self.updateKeys()
		self.run_console()

	def red(self):
		if self.commandIndex >= self.numberOfCommands:
			self.session.openWithCallback(self.removeAllLogfiles, MessageBox, _("Do you want to remove all the crash logfiles"), default=False)
		else:
			self.close()

	def green(self):
		if self.commandIndex >= self.numberOfCommands:
			try:
				remove(self.commands[self.commandIndex][4:])
			except (IOError, OSError) as err:
				pass
			self.updateOptions()
		self.run_console()

	def removeAllLogfiles(self, answer):
		if answer:
			for fileName in self.getLogFilesList():
				try:
					remove(fileName)
				except (IOError, OSError) as err:
					pass
			self.updateOptions()
			self.run_console()

	def appClosed(self, retval):
		if retval:
			self["AboutScrollLabel"].setText(_("An error occurred - Please try again later"))

	def dataAvail(self, data):
		self["AboutScrollLabel"].appendText(data)

	def run_console(self):
		self["AboutScrollLabel"].setText("")
		self.setTitle("%s - %s" % (_("Troubleshoot"), self.titles[self.commandIndex]))
		command = self.commands[self.commandIndex]
		if command.startswith("cat "):
			try:
				self["AboutScrollLabel"].setText(open(command[4:], "r").read())
			except (IOError, OSError) as err:
				self["AboutScrollLabel"].setText(_("Logfile does not exist anymore"))
		else:
			try:
				if self.container.execute(command):
					raise Exception("failed to execute: ", command)
			except Exception as err:
				self["AboutScrollLabel"].setText("%s\n%s" % (_("An error occurred - Please try again later"), err))

	def cancel(self):
		self.container.appClosed.remove(self.appClosed)
		self.container.dataAvail.remove(self.dataAvail)
		self.container = None
		self.close()

	def getDebugFilesList(self):
		import glob
		return [x for x in sorted(glob.glob("/home/root/logs/enigma2_debug_*.log"), key=lambda x: isfile(x) and getmtime(x))]

	def getLogFilesList(self):
		import glob
		home_root = "/home/root/logs/enigma2_crash.log"
		tmp = "/tmp/enigma2_crash.log"
		return [x for x in sorted(glob.glob("/mnt/hdd/*.log"), key=lambda x: isfile(x) and getmtime(x))] + (isfile(home_root) and [home_root] or []) + (isfile(tmp) and [tmp] or [])

	def updateOptions(self):
		self.titles = ["dmesg", "ifconfig", "df", "top", "ps", "messages"]
		self.commands = ["dmesg", "ifconfig", "df -h", "top -n 1", "ps -l", "cat /var/volatile/log/messages"]
		install_log = "/home/root/autoinstall.log"
		if isfile(install_log):
			self.titles.append("%s" % install_log)
			self.commands.append("cat %s" % install_log)
		self.numberOfCommands = len(self.commands)
		fileNames = self.getLogFilesList()
		if fileNames:
			totalNumberOfLogfiles = len(fileNames)
			logfileCounter = 1
			for fileName in reversed(fileNames):
				self.titles.append("logfile %s (%s/%s)" % (fileName, logfileCounter, totalNumberOfLogfiles))
				self.commands.append("cat %s" % (fileName))
				logfileCounter += 1
		fileNames = self.getDebugFilesList()
		if fileNames:
			totalNumberOfLogfiles = len(fileNames)
			logfileCounter = 1
			for fileName in reversed(fileNames):
				self.titles.append("debug log %s (%s/%s)" % (fileName, logfileCounter, totalNumberOfLogfiles))
				self.commands.append("tail -n 2500 %s" % (fileName))
				logfileCounter += 1
		self.commandIndex = min(len(self.commands) - 1, self.commandIndex)
		self.updateKeys()

	def updateKeys(self):
		self["key_red"].setText(_("Cancel") if self.commandIndex < self.numberOfCommands else _("Remove all logfiles"))
		self["key_green"].setText(_("Refresh") if self.commandIndex < self.numberOfCommands else _("Remove this logfile"))
