#!/usr/bin/env python
#DrawPi project etienne.8tn@gmail.com
#DrawPI is a minimalist vertical plotter based on
#Raspberry Pi and 28BYJ-48 motors.
#As input it uses a file with path coordinates.
#This file (name defined in svg_file_name variabe) is a subset of svg format
#to allow an easy visualisation through a web browser or inkscape.
#The svg file shall comply with the following syntax:
#only path method is to be used with absolute coordinates as following exemple:
#  <svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" name="image_svg.svg">
#    <path fill="none" stroke="black" d="M 10 0 L 200 0 L 200 200 L 0 200 L 0 0 L 10 0 " />
#  </svg>
#the above will draw a rectangle.
import time
import RPi.GPIO as GPIO
import math

#plotter variables
belt_pitch = 2.0   #belt pich in mm
pulley_tooth_nr = 20.0
steps_per_turn = 4076.0 #nr of stepper steps to get 1 full turn
motor_right_IOs = [24, 22, 18, 16] # A, B, C, D on blue; pink, yellow and orange stepper cables
motor_left_IOs = [15, 13, 11, 26] # A, B, C, D on blue; pink, yellow and orange stepper cables
pen_pwm = 12 # pwm IO pins for pen up and down servo
pwm_freq = 300 # pen pwm frequency, nominal 50, tested at 300
pwm_up_dc = 20 #pwm value to get the pen in up position (no drawing)
pwm_down_dc = 50 #pwm value to get the pen in down position (drawing)
pwm_time = 0.2 #time to change pwm position (time for the servo to reach its new position)
min_step_period = 0.001 #minimum step period between stepper motor steps (the lower the faster movement)
draw_resol = 1 #interpolation distance from x-Y cooredinates to pseudo polar coordinates
steps_ratio = steps_per_turn/(pulley_tooth_nr*belt_pitch) #steps per mm (101.9)
Do = 430.0 #horizontal distance between motors axes in mm
Pl = 200.0 #horizontal width of print area in mm
Ph = 200.0 #vertical height of print area in mm
Xo = (Do-Pl)/2 #hotizontal distance from left motor axle to border of print area in mm
Yo = 100.0 #vertical distance from motor axes to border of print area in mm
X_start = 115
Y_start = 100
Dl_dist = math.sqrt((X_start)*(X_start)+(Y_start)*(Y_start))
Dr_dist = math.sqrt((Do-X_start)*(Do-X_start)+(Y_start)*(Y_start))
last_x = 0
last_y = 0
M_steps = [[0,0,0,1], [0,0,1,1], [0,0,1,0], [0,1,1,0], [0,1,0,0], [1,1,0,0], [1,0,0,0], [1,0,0,1]]
l_motor_phase=0
r_motor_phase=0

#input file name
svg_file_name = "/home/pi/image_svg.svg"

#init GPIOs as outputs and to '0'
GPIO.setmode(GPIO.BOARD)
for a in range(4):
    GPIO.setup(motor_left_IOs[a], GPIO.OUT) 
    GPIO.output(motor_left_IOs[a], 0)
    GPIO.setup(motor_right_IOs[a], GPIO.OUT)
    GPIO.output(motor_right_IOs[a], 0)
for a in range(4) : GPIO.output(motor_left_IOs[a], M_steps[l_motor_phase][a])
for a in range(4) : GPIO.output(motor_right_IOs[a], M_steps[r_motor_phase][a])

#init servo GPIO and pen position is 'up'
GPIO.setup(pen_pwm, GPIO.OUT)
pwm = GPIO.PWM(pen_pwm, pwm_freq)
pwm.start(pwm_up_dc)
time.sleep(pwm_time)
pwm.ChangeDutyCycle(0)
time.sleep(pwm_time)

def v_lr_steps (l,r):
    global l_motor_phase,r_motor_phase
    i = max (abs(l), abs(r))
    for a in range(i):
        l_steps = ((a+1)*l/i)-(a*l/i)
        r_steps = ((a+1)*r/i)-(a*r/i)
        for a in range(4) : GPIO.output(motor_left_IOs[a], M_steps[l_motor_phase][a])
        l_motor_phase += l_steps
        if l_motor_phase == 8: l_motor_phase = 0
        if l_motor_phase == -1: l_motor_phase = 7
        for a in range(4) : GPIO.output(motor_right_IOs[a], M_steps[r_motor_phase][a])
        r_motor_phase+=r_steps
        if r_motor_phase == 8: r_motor_phase = 0
        if r_motor_phase == -1: r_motor_phase = 7
        time.sleep(min_step_period)

def v_lr_dist (x, y):
    global Dl_dist, Dr_dist
    Dl_next = math.sqrt(x*x+y*y)
    Left_steps = int(round((Dl_next - Dl_dist)*steps_ratio,0))
    Dl_change = Left_steps/steps_ratio 
    Dr_next = math.sqrt((Do-x)*(Do-x)+y*y)
    Right_steps = int(round((Dr_next - Dr_dist)*steps_ratio,0))
    Dr_change = Right_steps/steps_ratio
    v_lr_steps(-Left_steps, Right_steps)
    Dl_dist = Dl_next
    Dr_dist = Dr_next

def v_move (X_new, Y_new):
    global X_current, Y_current
    x = X_new - X_current
    y = Y_new - Y_current
    step_nr = math.sqrt(x*x + y*y)/draw_resol
    a = 1
    while math.sqrt((X_current-X_new)*(X_current-X_new)+(Y_current-Y_new)*(Y_current-Y_new)) >= draw_resol :
        X_next = (X_current+x/step_nr)
        Y_next = (Y_current+y/step_nr)
        v_lr_dist(X_next, Y_next)
        X_current = X_next
        Y_current = Y_next
        a+=1
    v_lr_dist(X_new, Y_new)
    X_current = X_new
    Y_current = Y_new

def pen_up():
    pwm.start(pwm_up_dc)
    time.sleep(pwm_time)
    pwm.ChangeDutyCycle(0)
    time.sleep(pwm_time)

def pen_down():
    pwm.start(pwm_down_dc)
    time.sleep(pwm_time)
    pwm.ChangeDutyCycle(0)
    time.sleep(pwm_time)

#main
try:
    svg_file = open(svg_file_name, 'r')
    line = svg_file.readline() #read first svg line to get size information
    widths = line.split("""width=""")[1].split(" ")[0]
    width = int(widths[1:len(widths)-1])
    heights = line.split("""height=""")[1].split(" ")[0]
    height = int(heights[1:len(heights)-1])
    scale = max(width/Pl, height/Ph) #in pxl per mm
    X_current = Xo
    Y_current = Yo
    line = svg_file.readline()
    while line:
        new_line = True
        path_valid = line.find("path")
        path_start = line.find(" d=")
        path_end = line.find(" /")
        if path_valid and path_start > 0 and path_end > 0 :
            path_str = line[path_start+5 : path_end-1]
            path_split = path_str.split("L")
            for i in range(len(path_split)):
                x=float(path_split[i][1:-1].split(" ")[0])
                y=float(path_split[i][1:-1].split(" ")[1])
                if new_line and (x!=last_x or y!=last_y): pen_up()
                #compute x and y using scale parameters
                X=Xo+(Pl-width/scale)/2+x/scale
                Y=Yo+(Ph-height/scale)/2+y/scale
                v_move(X,Y)
                if new_line and (x!=last_x or y!=last_y): pen_down()
                last_x = x
                last_y = y
                new_line = False
        line = svg_file.readline()
    svg_file.close()
    pen_up()
    v_move(Xo,Yo)
    GPIO.cleanup()
except KeyboardInterrupt: GPIO.cleanup()

