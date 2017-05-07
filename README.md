# setwifi
Enables the device's Access Point mode and serves a webpage for entering the SSID and password of a Wifi network to join.

This module can be either be called directly from the REPL, or can be called from code that determines that the device's WiFi configuration needs to be changed.

Usage:<br>
<code>
  from setwifi import setwifi; rc = setwifi()
</code>

where the returned string can be:
- "done: connected"
- "timeout"
- "exception: " + exception string
- "cancelled: attempts: " + N

Use-cases:
- initial deployment: the user has forever to enter the WiFi Info
- if changing to a new network, then pushing a reset button (vs power-on or deepsleep reset) can show the webpage for a limited time
- if the device can't connect to the network, the webpage can be shown

Tested on an ESP8266 running micropython: esp8266-20170108-v1.8.7
