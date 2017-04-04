#!/usr/bin/env python
import sys
import time, RPi.GPIO as GPIO
import math

#plotter variables
belt_pitch = 2.0   #belt pich in mm
pulley_tooth_nr = 20.0 #nr of teeth of the pulleys
steps_per_turn = 1026.0 #4076.0 #nr of stepper steps to get 1 full turn
motor_right_IOs = [16, 18, 22, 24] # A, B, C, D on blue; pink, yellow and orange stepper cables
motor_left_IOs = [26, 11, 13, 15] # A, B, C, D on blue; pink, yellow and orange stepper cables
min_step_period = 0.001 #0.001#minimum step period
#steps_per_turn = 4076.0 #nr of stepper steps to get 1 full turn
#motor_right_IOs = [24, 22, 18, 16] # A, B, C, D on blue; pink, yellow and orange stepper cables
#motor_left_IOs = [15, 13, 11, 26] # A, B, C, D on blue; pink, yellow and orange stepper cables
#min_step_period = 0.001 minimum step period
pen_pwm = 12 # pwm IO pins for pen up and down servo
pwm_freq = 300 # pen pwm frequency, nominal 50, tested at 300
pwm_up_dc = 20 #70 #19 to 84 at 300 Hz -> 70
pwm_down_dc = 50 #55 #19 to 84 at 300 Hz --> 60
pwm_time = 0.2 #0.3 sec time to change pwm position
draw_resol = 1.0 #required drawing resolution in mm
steps_ratio = steps_per_turn/(pulley_tooth_nr*belt_pitch) #steps per mm (101.9 or 25.65)

Do = 370.0 #370 for V2; 430.0for V1 #horizontal distance between motors axes in mm
Pl = 200.0 #horizontal width of print area in mm
Ph = 200.0 #vertical height of print area in mm
Xo = (Do-Pl)/2 #hotizontal distance from left motor axle to border of print area in mm
Yo = 100.0 #vertical distance from motor axes to border of print area in mm
X_start = 85.0 #85 for V2; 115 for V1
Y_start = 100.0
Dl_dist = math.sqrt((X_start)**2+(Y_start)**2) #in mm
Dr_dist = math.sqrt((Do-X_start)**2+(Y_start)**2) #in mm
Dl_steps = int(Dl_dist*steps_ratio)
Dr_steps = int(Dr_dist*steps_ratio)
last_x = 0.0
last_y = 0.0
#file manager variables
svg_file_name = "/var/www/html/multicambox_files/pirtraitiste/svg_picture.svg"
svg_file_name = "/home/pi/svg_carrex3.svg"
#svg_file_name = "/home/pi/svg_picture.svg"
svg_file_name = "/var/www/html/drawpi/svg_picture.svg"
#debug flags
db_v_main = True #main  debug flag
db_v_m = False #True #V_move function debug flag
db_v_scale = True #False #scale debug flag
db_v_lrd = False #V_lr_dist function debug flag
db_v_lrs = False #v_lr_steps function debug flag
db_r_svg = False #True #read_svg function debug flag
db_pen_ud = False #True #pen_up and pen_down functions debug flag

#init GPIOs as outputs and to '0'
GPIO.setmode(GPIO.BOARD)
for a in range(4):
	GPIO.setup(motor_left_IOs[a], GPIO.OUT) 
	GPIO.output(motor_left_IOs[a], 0)
	GPIO.setup(motor_right_IOs[a], GPIO.OUT)
        GPIO.output(motor_right_IOs[a], 0)

GPIO.setup(pen_pwm, GPIO.OUT)
pwm = GPIO.PWM(pen_pwm, pwm_freq)

pwm.start(pwm_up_dc)
time.sleep(pwm_time)
pwm.ChangeDutyCycle(0)
time.sleep(pwm_time)

M_steps = [[0,0,0,1], [0,0,1,1], [0,0,1,0], [0,1,1,0], [0,1,0,0], [1,1,0,0], [1,0,0,0], [1,0,0,1]]

l_motor_phase=0
for a in range(4) : GPIO.output(motor_left_IOs[a], M_steps[l_motor_phase][a])
r_motor_phase=0
for a in range(4) : GPIO.output(motor_right_IOs[a], M_steps[r_motor_phase][a])
if db_v_main: time.sleep(0.1)

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

def v_lr_dist (x, y): #coordinate to move in mm
    global Dl_steps, Dr_steps, steps_ratio
    next_l_steps = int(math.sqrt(x**2+y**2)*steps_ratio)
    next_r_steps = int(math.sqrt((Do - x)**2+y**2)*steps_ratio)
    left_steps = next_l_steps - Dl_steps
    right_steps = next_r_steps - Dr_steps
    v_lr_steps(-left_steps, right_steps)
    Dl_steps += left_steps
    Dr_steps += right_steps

def v_move (X_new, Y_new):#coordinate to move to in mm 
    global X_current, Y_current
    x = X_new - X_current
    y = Y_new - Y_current
    step_nr = math.sqrt(x*x + y*y)/draw_resol # nr of steps for linear interpolation
    a = 1
    while math.sqrt((X_current-X_new)**2+(Y_current-Y_new)**2) >= draw_resol :
        X_next = (X_current+x/step_nr)
        Y_next = (Y_current+y/step_nr)
        v_lr_dist(X_next, Y_next) #call for move to next interpolated point
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
    widths = line.split("""width=""")[1].split(" ")[0] #"""
    width = int(widths[1:len(widths)-1])
    heights = line.split("""height=""")[1].split(" ")[0] #"""
    height = int(heights[1:len(heights)-1])
    scale = max(width/Pl, height/Ph) #in pxl per mm
	
    X_current = Xo#+(Pl-width/scale)/2+width/2/scale
    Y_current = Yo#+(Ph-height/scale)/2+height/2/scale
    line = svg_file.readline()
    while line:
        new_line = True
        path_valid = line.find("path")
        path_start = line.find(" d=")
        path_end = line.find(" /")
        if path_valid and path_start > 0 and path_end > 0  :
            path_str = line[path_start+5 : path_end-1]
            path_split = path_str.split("L")
            for i in range(len(path_split)):
                if db_r_svg: 
                    print path_split[i][1:-1].split(" ")[0],
                    print path_split[i][1:-1].split(" ")[1]
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
    X=Xo+(Pl-width/scale)/2
    Y=Yo+(Ph-height/scale)/2
    v_move(X_start,Y_start)
    GPIO.cleanup()
except KeyboardInterrupt: GPIO.cleanup()

