'''
NOTES:
L239D TPLH: 800 ns
Stepper Motor LR time constant: .0033/34 ~ .0001s
2N2222 delay time: 10ns
       fall time: 60ns
~LR time constant is slowest portion~
 - Did not take into account mechanical rotation time
 - Mechanical rotation allows for around 2 R/sec

With only factoring LR time constant:
 - max sec per inch = LR time constant * 200 step/rev
   * 20 rev/inch = .3888 sec/inch
Factoring in mechanical time delay:
 - 1/10th inch/sec = 2 R/sec * 1/20 inch/R
 ~ 10 sec / inch ~

power_on(), power_off(), GPIO.setup(), GPIO initiation silenced for debugging 
'''


#import RPi.GPIO as GPIO
import time
from queue import Queue
from math import sqrt, pow
import threading

# global variables #
off_time = .00125
##

class Printer(object):
    def __init__(self, x_m_pins, y_m_pins, z_m_pins):
        self.speed_cm_sec = 1/10*2.54
        self.axis = {}
        self.axis['x'] = Motor('x',x_m_pins[0],\
        x_m_pins[1], x_m_pins[2], x_m_pins[3])
        self.axis['y'] = Motor('y',y_m_pins[0],\
        y_m_pins[1], y_m_pins[2], y_m_pins[3])
        self.axis['z'] = Motor('z',z_m_pins[0],\
        z_m_pins[1], z_m_pins[2], z_m_pins[3])
        self.instructions = Queue()
    def build_instructions(self, points):
        current_point = [0,0,0]
        # assuming current position is (0,0,0)
        for point in points:
            x_trans = (current_point[0] - point[0])
            y_trans = (current_point[1] - point[1])
            z_trans = (current_point[2] - point[2])
            xy_time = max(abs(x_trans), abs(y_trans))\
                      /self.speed_cm_sec
            z_time = abs(z_trans)/self.speed_cm_sec
            x_steps = round(x_trans/2.54*20*200)
            y_steps = round(y_trans/2.54*20*200)
            z_steps = round(z_trans/2.54*20*200)
            if z_steps != 0:
                self.instructions.put(Motor_Instruction\
                                      (0,z_time, 'y'))
                self.instructions.put(Motor_Instruction\
                                      (0,z_time, 'x'))
                self.instructions.put(Motor_Instruction\
                                      (z_steps,z_time, 'z'))
            self.instructions.put(Motor_Instruction\
                                  (x_steps,xy_time, 'x'))
            self.instructions.put(Motor_Instruction\
                                  (y_steps,xy_time, 'y'))
            self.instructions.put(Motor_Instruction\
                                  (0,xy_time, 'z'))
            current_point = point
    def print_model(self, points):
        self.build_instructions(points)
        operator_1 = threading.Thread(target = self.operator)
        operator_2 = threading.Thread(target = self.operator)
        operator_3 = threading.Thread(target = self.operator)
        self.checker = Sychronisation_check()
        start = time.time()
        operator_1.start()
        operator_2.start()
        operator_3.start()
        operator_1.join()
        operator_2.join()
        operator_3.join()
        end = time.time()
        print('time: ', end - start)
        print(self.checker.total_time_between_operators)
    def operator(self):
        while not self.instructions.empty():
            instruction = self.instructions.get()
            print('begin time for axis', instruction.axis, time.time())
            if instruction.steps == 0:
                print('sleeping')
                time.sleep(instruction.total_time)
            else:
                self.axis[instruction.axis].translate(instruction.steps, \
                instruction.on_time_per_step, instruction.direction)
            self.instructions.task_done()
            self.checker.lock.acquire()
            self.checker.completed_task()
            self.checker.lock.release()
            print('end time for axis', instruction.axis, time.time())
class Motor_Instruction(object):
    def __init__(self, steps, seconds, axis):
        self.steps = abs(steps)
        if steps > 0:
            self.direction = 1
        else:
            self.direction = 0
        self.axis = axis
        total_off_time = off_time*self.steps
        self.on_time = float(seconds) - total_off_time
        if steps == 0:
            self.on_time_per_step = 0
        else:
            self.on_time_per_step = self.on_time/self.steps
        self.total_time = seconds
        print(self.steps*(off_time + self.on_time_per_step), seconds)
    def __str__(self):
        string = self.axis + ':\n' + \
        'on time per step: ' + str(self.on_time_per_step) + '\n'\
        + 'on time total: ' + str(self.on_time) + '\n'\
        + 'total time: ' + str(self.total_time) + '\n'\
        + 'direction: ' + str(self.direction) + '\n'\
        + 'steps:' + str(self.steps) + '\n'
        return string
class Motor(object):
    def __init__(self, axis, p1, p2, p3, p4):
        self.axis = axis
        self.sol1 = Solenoid(p1, p2)
        self.sol2 = Solenoid(p3, p4)
        self.steps_per_rotation = 360/1.8
        self.one_rotation = 1/20 # inches
        self.operation_complete = False
        self.motor_key = threading.Lock()
        self.power_down()
        print('Motor initiated:')
        print('Pin 1:', self.sol1.pin1)
        print('Pin 2:', self.sol1.pin2)
        print('Pin 3:', self.sol2.pin1)
        print('Pin 4:', self.sol2.pin2)
    def step(self, phase, power_time, sol):
        print('power time', power_time, 'phase', phase, 'sol', sol)
        start = time.time()
        if sol == 1:
            #self.sol1.power_on(phase)
            time.sleep(.00125)
            end = time.time()
            print('step time: ', end - start)
            #self.sol1.power_off()
        elif sol == 2:
            #self.sol2.power_on(phase)
            time.sleep(.00125)
            #self.sol2.power_off()
        time.sleep(.00125)
        end = time.time()
        print('step time: ', end - start)
    def translate(self, steps, on_time_per_step, direction):
        phase = 0
        sol = 1
        if direction == 1:
            phase = 0
            sol = 1
            print('about to step')
            print(on_time_per_step, steps)
            for counts in range(steps):
                self.step(phase, on_time_per_step, sol)
                if phase == 0:
                    if sol == 2:
                        sol = 1
                        phase = 1
                    else:
                        sol = 2
                elif phase == 1:              
                    if sol == 2:
                        sol = 1
                        phase = 0
                    else:
                        sol = 2
        else:
            phase = 1
            sol = 2
            print('about to step')
            for counts in range(steps):
                self.step(phase, on_time_per_step, sol)
                if phase == 0:
                    if sol == 2:
                        sol = 1
                    else:
                        sol = 2
                        phase = 1
                elif phase == 1:               
                    if sol == 2:
                        sol = 1
                    else:
                        sol = 2
                        phase = 0
        print('time for loops: ', end - start, 'expected time:', (steps*(on_time_per_step + .00125)))
    def power_down(self):
        pass
        #self.sol1.power_off()
        #self.sol2.power_off()
class Solenoid(object):
    def __init__(self, pin1, pin2):
        self.time_consant = .0033/34
        self.pin1 = pin1
        self.pin2 = pin2
        self.sol_high = 1
        self.sol_low = 0
        self.is_powered = False
        #GPIO.setup(self.pin1, GPIO.OUT)
        #GPIO.setup(self.pin2, GPIO.OUT)
    def power_on(self, direction):
        # until a direction is found via
        # testing, direction is arbitrary
        if direction == 0:
            GPIO.output(self.pin2, \
                         self.sol_low)
            GPIO.output(self.pin1, \
                         self.sol_high)
        elif direction == 1:
            GPIO.output(self.pin1, \
                         self.sol_low)
            GPIO.output(self.pin2, \
                         self.sol_high)
        self.is_powered = True
    def power_off(self):
        GPIO.output(self.pin1, \
                    self.sol_low)
        GPIO.output(self.pin2, \
                    self.sol_low)
        self.is_powered = False
class Sychronisation_check(object):
    def __init__(self):
        self.adder = 0
        self.total_time_between_operators = []
        self.delay_timer_start = 0
        self.delay_timer_end = 0
        self.lock = threading.Lock()
    def completed_task(self):
        self.adder += 1
        self.check_adder()
    def check_adder(self):
        if self.adder == 1:
            self.delay_timer_start = time.time()
        if self.adder == 3:
            self.delay_timer_end = time.time()
            self.total_time_between_operators.\
            append(self.delay_timer_end - self.delay_timer_start)
            self.adder = 0
        if self.adder > 3:
            raise('adder greater than 3')
    
    
#GPIO.setmode(GPIO.BCM)

printer = Printer([19, 26, 20, 21], [24, 12, 18, 23], [17, 22, 5, 6], )
time.sleep(1)
instructions = [[1,1,0], [0,0, 0]]
input('Enter to initiate')

printer.print_model(instructions)
#GPIO.cleanup()