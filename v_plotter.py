#!/usr/bin/env python
#DrawPi project etienne.8tn@gmail.com
import sys
import time, RPi.GPIO as GPIO
import math

#plotter variables
belt_pitch = 2.0   #belt pich in mm
pulley_tooth_nr = 20.0
steps_per_turn = 4076.0 #nr of stepper steps to get 1 full turn
motor_right_IOs = [24, 22, 18, 16] # A, B, C, D on blue; pink, yellow and orange stepper cables
motor_left_IOs = [15, 13, 11, 26] # A, B, C, D on blue; pink, yellow and orange stepper cables
pen_pwm = 12 # pwm IO pins for pen up and down servo
pwm_freq = 300 # pen pwm frequency, nominal 50, tested at 300
pwm_up_dc = 70 #19 to 84 at 300 Hz -> 70
pwm_down_dc = 55 #19 to 84 at 300 Hz --> 60
pwm_time = 0.3 #time to change pwm position
min_step_period = 0.001 #minimum step period
draw_resol = 1 #required drawing resolution in mm
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
#Dl_dist = math.sqrt((Xo+Pl/2)*(Xo+Pl/2)+(Yo+Ph/2)*(Yo+Ph/2))
#Dr_dist = math.sqrt((Do-Xo-Pl/2)*(Xo+Pl/2)+(Yo+Ph/2)*(Yo+Ph/2))
last_x = 0
last_y = 0
#file manager variables
svg_file_name = "/home/pi/image_svg.svg"
#debug flags
db_v_main = True #main  debug flag
db_v_m = False #V_move function debug flag
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

if db_pen_ud: print "jump move UP UP UP UP -> ", pwm_up_dc
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
        if db_v_lrs: print "    v_lr_steps() starts", l, r
	i = max (abs(l), abs(r))
	if db_v_lrs: print "    v_lr_steps() max", i
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
		if db_v_lrs: print "    v_lr_steps() max", a, l_steps, r_steps, "-", l_motor_phase, r_motor_phase

def v_lr_dist (x, y):
	global Dl_dist, Dr_dist
	Dl_next = math.sqrt(x*x+y*y)
        Left_steps = int(round((Dl_next - Dl_dist)*steps_ratio,0))
	Dl_change = Left_steps/steps_ratio 
	Dr_next = math.sqrt((Do-x)*(Do-x)+y*y)
        Right_steps = int(round((Dr_next - Dr_dist)*steps_ratio,0))
	Dr_change = Right_steps/steps_ratio
        if db_v_lrd:
        	print "  v_lr_dist() starts", round(x, 2), round(y, 2), 
		print "L", round(Dl_dist, 2), round(Dl_next, 2), round(Dl_change, 2), Left_steps,
                print "R", round(Dr_dist, 2), round(Dr_next, 2), round(Dr_change, 2), Right_steps
	v_lr_steps(-Left_steps, Right_steps)
	Dl_dist = Dl_next
	Dr_dist = Dr_next
        if db_v_lrd: print "  v_lr_dist() ended"

def v_move (X_new, Y_new):
	global X_current, Y_current
        x = X_new - X_current
        y = Y_new - Y_current
        if db_v_m: 
		print " v_move() called", round(X_current, 2), round(Y_current, 2),
		print "->", round(X_new, 2), round(Y_new, 2), ":", x, y
	step_nr = math.sqrt(x*x + y*y)/draw_resol
        if db_v_m: print " v_move() step nr", round(step_nr, 2)
	a = 1
        while math.sqrt((X_current-X_new)*(X_current-X_new)+(Y_current-Y_new)*(Y_current-Y_new)) >= draw_resol :
		X_next = (X_current+x/step_nr)
		Y_next = (Y_current+y/step_nr)
                if db_v_m: print " v_move() executes", a, round(X_next, 2), round(Y_next, 2), X_new, Y_new,
                if db_v_m: print "~~", Dl_dist, Dr_dist 
		v_lr_dist(X_next, Y_next)
		X_current = X_next
		Y_current = Y_next
		a+=1
	if db_v_m: print " v_move() finalizes", X_new, Y_new
	v_lr_dist(X_new, Y_new)
        X_current = X_new
        Y_current = Y_new
        if db_v_m: print " v_move() ended"

def pen_up():
	if db_pen_ud: print "jump move UP UP UP UP", pwm_up_dc
        pwm.start(pwm_up_dc)
        time.sleep(pwm_time)
        pwm.ChangeDutyCycle(0)
        time.sleep(pwm_time)

def pen_down():
	if db_pen_ud: print "jump move DOWN DOWN DOWN", pwm_down_dc
        pwm.start(pwm_down_dc)
        time.sleep(pwm_time)
        pwm.ChangeDutyCycle(0)
        time.sleep(pwm_time)

#main
try:
	if db_v_main: print "main starts"
	if db_r_svg or db_v_main: print "read_svg starts", svg_file_name
        svg_file = open(svg_file_name, 'r')

        line = svg_file.readline() #read first svg line to get size information
	if db_v_main: print line
	widths = line.split("""width=""")[1].split(" ")[0] #"""
	width = int(widths[1:len(widths)-1])
	heights = line.split("""height=""")[1].split(" ")[0] #"""
	height = int(heights[1:len(heights)-1])
	scale = max(width/Pl, height/Ph) #in pxl per mm
	if db_v_scale: print "width", width, "height", height, "scale", scale

#	x=320
#	y=240
#	if db_v_scale: print "x=", x, "-> X",Xo+(Pl-width/scale)/2+x/scale
#	if db_v_scale: print "y=", y, "-> Y",Yo+(Ph-height/scale)/2+y/scale
#	if db_v_scale: print "-"
	
	X_current = Xo#+(Pl-width/scale)/2+width/2/scale
	Y_current = Yo#+(Ph-height/scale)/2+height/2/scale
	if db_v_main: print "init pos:", X_current, Y_current
	line = svg_file.readline()
	while line:
		new_line = True
		path_valid = line.find("path")
		path_start = line.find(" d=")
                path_end = line.find(" /")
		if db_r_svg: print "line:", line[:-1], " -> ", line.find("""d="M"""), path_start, path_end
		if path_valid and path_start > 0 and path_end > 0  :
			path_str = line[path_start+5 : path_end-1]
                        if db_r_svg: print "path_str:", path_str
			path_split = path_str.split("L")
                        if db_r_svg: print "path_split:", path_split, len(path_split)
			for i in range(len(path_split)):
				if db_r_svg: 
					print path_split[i][1:-1].split(" ")[0],
					print path_split[i][1:-1].split(" ")[1]
				x=float(path_split[i][1:-1].split(" ")[0])
				y=float(path_split[i][1:-1].split(" ")[1])
				if new_line and (x!=last_x or y!=last_y): pen_up()
                                if db_r_svg or db_v_main: print "path_move:", x, y, #new_line, last_x, last_y
				#compute x and y using scale parameters
				X=Xo+(Pl-width/scale)/2+x/scale
				Y=Yo+(Ph-height/scale)/2+y/scale
				if db_v_scale: print "pathscale", X, Y
				v_move(X,Y)
				if new_line and (x!=last_x or y!=last_y): pen_down()
				last_x = x
				last_y = y
				new_line = False
                line = svg_file.readline()
        svg_file.close()
	pen_up()
	if db_v_scale: print "pathscale", X_start, Y_start
	v_move(Xo,Yo)
	if db_r_svg: print "read_svg ends"
	if db_v_main: print "main ends", round(X_current, 2), round(Y_current, 2)
        GPIO.cleanup()
except KeyboardInterrupt: GPIO.cleanup()

