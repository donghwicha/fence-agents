#!/usr/bin/python

#####
##
## The Following Agent Has Been Tested On:
##
##  DRAC Version       Firmware
## +-----------------+---------------------------+
##  DRAC 5             1.0  (Build 06.05.12)
##  DRAC 5             1.21 (Build 07.05.04)
##
## @note: drac_version was removed
#####

import sys, re, pexpect, exceptions, time
sys.path.append("@FENCEAGENTSLIBDIR@")
from fencing import *

#BEGIN_VERSION_GENERATION
RELEASE_VERSION="New Drac5 Agent - test release on steroids"
REDHAT_COPYRIGHT=""
BUILD_DATE="March, 2008"
#END_VERSION_GENERATION

def get_power_status(conn, options):
	if options["model"] == "DRAC CMC":
		conn.send_eol("racadm serveraction powerstatus -m " + options["--module-name"])
	elif options["model"] == "DRAC 5":
		conn.send_eol("racadm serveraction powerstatus")
		
	conn.log_expect(options, options["--command-prompt"], int(options["--shell-timeout"]))
				
	status = re.compile("(^|: )(ON|OFF|Powering ON|Powering OFF)\s*$", re.IGNORECASE | re.MULTILINE).search(conn.before).group(2)
	if status.lower().strip() in ["on", "powering on", "powering off"]:
		return "on"
	else:
		return "off"

def set_power_status(conn, options):
	action = {
		'on' : "powerup",
		'off': "powerdown"
	}[options["--action"]]

	if options["model"] == "DRAC CMC":
		conn.send_eol("racadm serveraction " + action + " -m " + options["--module-name"])
	elif options["model"] == "DRAC 5":
		conn.send_eol("racadm serveraction " + action)
	conn.log_expect(options, options["--command-prompt"], int(options["--power-timeout"]))

def get_list_devices(conn, options):
	outlets = { }

	if options["model"] == "DRAC CMC":
		conn.send_eol("getmodinfo")

		list_re = re.compile("^([^\s]*?)\s+Present\s*(ON|OFF)\s*.*$")
		conn.log_expect(options, options["--command-prompt"], int(options["--power-timeout"]))
		for line in conn.before.splitlines():
			if (list_re.search(line)):
				outlets[list_re.search(line).group(1)] = ("", list_re.search(line).group(2))
	elif options["model"] == "DRAC 5":
		## DRAC 5 can be used only for one computer
		## standard fence library can't handle correctly situation
		## when some fence devices supported by fence agent
		## works with 'list' and other should returns 'N/A'
		print "N/A"

	return outlets
	
def main():
	device_opt = [  "ipaddr", "login", "passwd", "passwd_script",
			"cmd_prompt", "secure", "identity_file", "drac_version", "module_name",
			"separator", "inet4_only", "inet6_only", "ipport" ]

	atexit.register(atexit_handler)

	all_opt["cmd_prompt"]["default"] = [ "\$" ]

	options = check_input(device_opt, process_input(device_opt))

	docs = { }           
	docs["shortdesc"] = "Fence agent for Dell DRAC CMC/5" 
	docs["longdesc"] = "fence_drac5 is an I/O Fencing agent \
which can be used with the Dell Remote Access Card v5 or CMC (DRAC). \
This device provides remote access to controlling  power to a server. \
It logs into the DRAC through the telnet/ssh interface of the card. \
By default, the telnet interface is not  enabled."
	docs["vendorurl"] = "http://www.dell.com"
	show_docs(options, docs)

	##
	## Operate the fencing device
	######
	conn = fence_login(options)

	if conn.before.find("CMC") >= 0:
		if 0 == options.has_key("--module-name") and 0 == ["monitor", "list"].count(options["--action"].lower()):
			fail_usage("Failed: You have to enter module name (-m)")
			
		options["model"] = "DRAC CMC"
	elif conn.before.find("DRAC 5") >= 0:
		options["model"] = "DRAC 5"
	else:
		## Assume this is DRAC 5 by default as we don't want to break anything
		options["model"] = "DRAC 5"

	result = fence_action(conn, options, set_power_status, get_power_status, get_list_devices)

	##
	## Logout from system
	######
	try:
		conn.send_eol("exit")
		time.sleep(1)
		conn.close()
	except:
		pass
	
	sys.exit(result)

if __name__ == "__main__":
	main()
