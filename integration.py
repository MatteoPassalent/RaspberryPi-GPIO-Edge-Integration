import RPi.GPIO as GPIO
import smbus
import time
import datetime

def motor_control_mode():
    """
    Couples the rotation angle of the servo motor with the angle of the potentiometer.
    """
    ADC_ADDR = 0x48
    POTENTIOMETER_ADDR = 0x43 #Potentiometer, output voltage changes linearly
    GPIO18 = 18 # PWM pin for servo motor

    bus = smbus.SMBus(1)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO18, GPIO.OUT)
    p = GPIO.PWM(GPIO18, 50) # PWM frequency of 50 Hz
    p.start(7.5) # Start in neutral position

    prev_value = None  
    try:
        while True:
            bus.write_byte(ADC_ADDR, POTENTIOMETER_ADDR)
            value = bus.read_byte(ADC_ADDR)
            if value != prev_value:
                # Convert (0-255) value to porportional angle (0-180)
                angle = round((value / 255) * 180)
                print("Arm Angle (degrees):", angle)
            # Convert (0-255) value to porportional duty cycle of (2.5-10.5)
            duty_cycle = 2.5 + (value / 255) * (10.5 - 2.5)
            p.ChangeDutyCycle(duty_cycle)
            prev_value = value
    except KeyboardInterrupt:
        pass
    p.stop()
    GPIO.cleanup()

def distance_detection_mode():
    """
    Detects the distance of an object in front of the sensor
    and adjust the brightness of an LED based on the distance.
    """
    TRIGGER_PIN=26
    ECHO_PIN=19
    LED_PWM_PIN=12
    HIGH_TIME=0.00001 # Adjusted trigger pulse length
    LOW_TIME=1-HIGH_TIME
    SPEED_OF_SOUND=330/float(10000) # Speed of sound in air 330m/s -> 0.033 cm/microsecond

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_PWM_PIN, GPIO.OUT)
    GPIO.setup(TRIGGER_PIN,GPIO.OUT)
    GPIO.setup(ECHO_PIN,GPIO.IN)
    p = GPIO.PWM(LED_PWM_PIN, 40) # PWM frequency of 40 Hz
    p.start(0) # Start with 0 duty cycle

    def get_distance(travel_time):
        distance = SPEED_OF_SOUND * travel_time / float(2) # Calculate distance in cm
        return round(distance)
    try:
        while True:
            # Send 10 microsecond pulse
            GPIO.output(TRIGGER_PIN,GPIO.HIGH)
            time.sleep(HIGH_TIME)
            GPIO.output(TRIGGER_PIN,GPIO.LOW)

            # Wait for echo to start
            while GPIO.input(ECHO_PIN) == False:
                pass
            start_time = datetime.datetime.now().microsecond

            # Wait for echo to end
            while GPIO.input(ECHO_PIN) == True:
                pass
            end_time = datetime.datetime.now().microsecond

            travel_time = end_time - start_time
            distance = max(min(get_distance(travel_time), 30), 0) # clamp distance between 0 and 30
            print("Distance(cm):", distance if distance < 30 else "30+") # Max distance is 30 cm
            duty_cycle = 100 - (distance / 30) * 100 # Calculate duty cycle and inverse
            p.ChangeDutyCycle(duty_cycle)
            time.sleep(LOW_TIME)
    except KeyboardInterrupt:
            pass
    p.stop()
    GPIO.cleanup()

try:
    while True:
        print("Choose User Mode")
        print("1: Motor Control Mode")
        print("2: Distance Detection Mode")
        print("exit: Exit Program")
        user_input = input("Please select a mode: ")
        if user_input == "1":
            print("Entering Motor Control Mode, press ctrl+c to return to main menu")
            motor_control_mode()
            print("Exiting Motor Control Mode")
        elif user_input == "2":
            print("Entering Distance Detection Mode, press ctrl+c to return to main menu")
            distance_detection_mode()
            print("Exiting Distance Detection Mode")
        elif user_input == "exit":
            break
except KeyboardInterrupt:
    pass
