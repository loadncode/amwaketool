<h1>Introduction</h1>

amwaketool enables the "Wake up" function in the Kore and Yatse Android and iOS apps. This means that Kodi running on Linux devices can be started remotely from Kore or Yatse.

amwaketool runs Kodi from within the active user's session (and with the active user's permissions) to ensure that Kodi features such as device power management work. amwaketool can be installed on multiple devices within the same LAN without conflicting. amwaketool also functions across different GUI user login sessions and does not conflict with local (non-remote) methods of starting Kodi.

Note that amwaketool requires root permissions by default because it listens on UDP port 9 which is a priviledged port.

<h1>Compatibility</h1>
amwaketool should work on Linux distros, it has been tested on Debian and Arch. Not tested on Raspberry Pi yet.

Presently amwaketool is only compatible with Python 2.x and not Python 3.x.

Technically either systemd-logind or ConsoleKit is required but practically all distros use at least one of these.

<h1>Dependencies</h1>

amwaketool requires the following Python 2.x modules:

  * dbus-python ("python-dbus" in Debian repository)
  * PyGObject ("python-gi" in Debian repository)
  * netifaces

You can either install these with pip or (if available) via your distro's repositories. Exact module names may vary between distro repositories. To install via pip run:

"pip install dbus-python PyGObject netifaces"


<h1>Installing / Uninstalling</h1>

* git clone https://github.com/loadncode/amwaketool.git
* cd amwaketool
* ./install (ideally run from a local session and as superuser, not actual root)

* To uninstall run ./install --uninstall

<h1>Autostarting</h1>

The install script sets up a systemd unit and configures it to autostart on boot. If you don't want this behaviour, run this command as root:
"systemctl disable amwaketool.service"

<h1>Technical information</h1>

This section gives a more detailed account of how amwaketool works. Firstly the amwaketool systemd service starts amwaketool.py which functions as the Wake-on-Lan server. It is run as root because Kore/Yatse use UDP port 9 for WoL packets by default which is a privileged port (all ports < 1024 need root permissions).

When amwaketool thinks it may have received WoL packets, it attempts to validate them, mainly by checking the destination MAC address contained in them against the actual one of your network adaptor. Note that at present this feature is only coded to work for 48-bit MAC addresses (the vast majority) and IPv4 connections (again, the large majority).

Once it has validated the packets, amwaketool attempts to connect to Kodi's (localhost) JSON-RPC server to ensure that there is not already another instance of Kodi running. This catches Kodi instances started via amwaketool as well as, for example, ones started directly from your desktop environment.

amwaketool then checks which login session is both the active and local one using either systemd-logind or ConsoleKit. It then lowers its privileges to the UID/GID of the active and local session. It then connects to this user's D-Bus Session Bus and uses D-Bus Activation to start the org.amwaketool D-Bus service. Finally it tells org.amwaketool to start Kodi in the user's X11 session.

Note that the way that amwaketool.py connects to the Session Bus is by reading "\~/.amwaketool/dbus_session_bus_address". This file is created/updated on each user's X11 login by the bash script "amwaketool-get-bus-addr". It only works if you have the environment variable $DBUS_SESSION_BUS_ADDRESS present in your X11 environment, which it should be. There also exists "\~/.dbus/session-bus/*" which is written by D-Bus itself but I have found the information contained in these files to be inconsistent and/or outdated (hence I didn't use them).

<h1>Misc</h1>

Neither amwaketool or it's developer are associated with Yatse, Kodi, or Kore.

License file requires gzip decompression to read.
