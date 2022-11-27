# Apply different PWM settings
# Measure temperatures, RH values
# MicroPython v1.19.1 on Raspberry Pi Pico W
# J.Beale 10pm 26-Nov-2022

from time import sleep
import ujson         # network secrets in json format
from machine import ADC, Pin, PWM, reset
import AHTp  # custom: read pair of AHT10 sensors
import MQ    # custom: connect wifi and MQTT

dtime = 50  # PWM update delay time in seconds
#dtime = 1  # PWM update delay time in seconds
step = 2500      # PWM 16-bit increment per cycle
pMax = int(65535) # PWM maximum value
pMin = int(200)   # PWM maximum value

# drive levels as a fraction of maximum PWM output
a0 = 0
a1 = 0.005
a2 = 0.03
a3 = 0.1
a4 = 0.25
a5 = 0.35
a6 = 0.60

# set each drive level in sequence
drive = (a1,a2,a3,a4,a6,a1,a0,a0,-a1,-a2,-a3,-a4,-a5,-a3,-a1,a0)

def blinkSignal(n,time):    # blink LED n times with delay 'time'
    for i in range(n):
        led.on()
        sleep(time)
        led.off()
        sleep(time)

def doPwmSet(val):  # set correct PWM output channel and level
    if (val == 0):
        p1.duty_u16(0)
        p2.duty_u16(0)
    elif (val > 0):
        if (p2.duty_u16() != 0):
            p2.duty_u16(0)
        p1.duty_u16(val)
    else:
        if (p1.duty_u16() != 0):
            p1.duty_u16(0)
        p2.duty_u16(-val)

def getPtemp():  # read internal Pico temperature
    picoRawT = sensorTemp.read_u16() * degCfactor
    degC = 27 - (picoRawT - 0.706)/0.001721
    msg = "%.1f, " % (degC) # Pico internal temp
    return msg

# =============================================
p1 = PWM(Pin(12))  # set up PWM output pins
p2 = PWM(Pin(13))
p1.freq(1000)
p2.freq(1000)
p1.duty_u16(0)
p2.duty_u16(0)

led = Pin('LED', Pin.OUT)  # onboard LED for signals

sensorTemp = ADC(4)   # Pico internal temp
degCfactor = 3.3 / (65535) # conversion factor

S = AHTp.AHTPair()  # create AHT10 sensor read object
S.initSensors([17,16,15,14]) # scl1,sda1, scl2,sda2
avgCount = 5  # how many readings to average together
cycleCount = 0 # full cycle index number
# =============================================
# Start wifi, MQTT

blinkSignal(2,0.75) # start up indicator


with open('secrets.json') as fp:  # network credentials
    secrets = ujson.loads(fp.read())

mq=MQ.MQTTobject() # wifi + MQTT
mq.initWLAN(secrets)  # start up wifi link
try:  # make MQTT connection
   client = mq.mqtt_connect(secrets)
except OSError as e:
   blinkSignal(8,0.1) # error indicator
   reconnect()

topic_pub =  'PT'            # MQTT topic to publish under
sParts = 6               # divide PWM steps into this many report intervals
# ------------------------------------------



while True:
    try:
        cycleCount += 1  # start a new full cycle
        stepCount = 0
        doPwmSet(0)
        blinkSignal(4,0.25)
        for d in drive:    
            pwmValue = int(pMax * d)
            stepCount += 1
            pString = ("%05d, %02d, %05d, " % (cycleCount,stepCount,pwmValue))
            doPwmSet(pwmValue)
            for t in range(sParts):
                sleep(dtime/sParts)
                msg = getPtemp()
                outs = pString + msg + S.getTH(avgCount)
                print(outs)        
                client.publish(topic_pub, outs)
    except OSError:
        print("Encountered OSError in main loop")
        reset()