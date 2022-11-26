# Pi Pico W: report internal temperature through MQTT

# based on:
# https://www.tomshardware.com/how-to/send-and-receive-data-raspberry-pi-pico-w-mqtt
# github.com/micropython/micropython-lib/blob/master/micropython/umqtt.simple/umqtt/simple.py
# J.Beale 26-Nov-2022

# local 'secrets.json' file in this format:
"""
{
  "wifi": {"ssid" : "MyWifiName","pass": "MyWifiPassword"}
  "mqtt": {"server": "MyMQTTBroker","user": "LocalDeviceName"}
}
"""

import network
import time
from machine import ADC, Pin, reset
from umqtt.simple import MQTTClient
import ujson
import AHTp  # custom: read pair of AHT10 sensors

with open('secrets.json') as fp:
    secrets = ujson.loads(fp.read())
    
ssid = secrets['wifi']['ssid']     # my wifi router name
password = secrets['wifi']['pass'] # my wifi password

mqtt_server = secrets['mqtt']['server']
client_id =   secrets['mqtt']['user']
topic_pub =  'PT'

#print("Read SSID as: %s" % ssid)
#print("Read client ID as: %s" % client_id)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    wlan.connect(ssid, password)
while wlan.isconnected() == False:
    print('Waiting for connection...')
    time.sleep(2)
print(wlan.ifconfig())


def mqtt_connect():
    print("MQTT connect attempt: %s %s" % (client_id, mqtt_server))
    client = MQTTClient(client_id, mqtt_server, keepalive=3600)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    return client

def reconnect():
   print('Failed to connect to the MQTT Broker.')
   time.sleep(5)
   # reset()

try:
   client = mqtt_connect()
except OSError as e:
   reconnect()

# --- Read sensor and report data
# =============================================

sensorTemp = ADC(4) 
degCfactor = 3.3 / (65535) 

print("Tpico, T0,T1, RH0,RH1")

avgCount = 5  # how many readings to average together

S = AHTp.AHTPair()  # create AHT10-Pair sensor reading object
S.initSensors([17,16,15,14]) # scl1,sda1, scl2,sda2

while True:
    reading = sensorTemp.read_u16() * degCfactor
    degC = 27 - (reading - 0.706)/0.001721
    msg = "%.1f, " % (degC) # Pico internal temp
    
    outs = msg + S.getTH(avgCount)
    print(outs)

    client.publish(topic_pub, outs)

  
