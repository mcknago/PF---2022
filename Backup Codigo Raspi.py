import os
import time
import datetime
import board
import digitalio
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219
from mcp3008 import MCP3008
import adafruit_mcp4725
import adafruit_ina260

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

i2c_bus = board.I2C()

intento=True
while intento:
    try:
        ina2191 = INA219(i2c_bus, 0x40)
        ina2195 = INA219(i2c_bus, 0x42)
        ina2192 = INA219(i2c_bus, 0x44)
        ina2193 = INA219(i2c_bus, 0x41)
        ina2194 = INA219(i2c_bus, 0x45)
        ina2601 = adafruit_ina260.INA260(i2c_bus, 0x43)
        ina2602 = adafruit_ina260.INA260(i2c_bus, 0x46)
        ina2603 = adafruit_ina260.INA260(i2c_bus, 0x47)
        intento = False
    except:
        print('Se descalibraron los sensores...Dormiré 30 segundos...')
        time.sleep(30)
        
dac_setpoint = adafruit_mcp4725.MCP4725(i2c_bus, address=0x61)

# Configuration to use 32 samples averaging for both bus voltage and shunt voltage
ina2191.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2191.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2192.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2192.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2193.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2193.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2194.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2194.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2195.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina2195.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S

# Change voltage range to 32V
ina2191.bus_voltage_range = BusVoltageRange.RANGE_32V
ina2192.bus_voltage_range = BusVoltageRange.RANGE_32V
ina2193.bus_voltage_range = BusVoltageRange.RANGE_32V
ina2194.bus_voltage_range = BusVoltageRange.RANGE_32V
ina2195.bus_voltage_range = BusVoltageRange.RANGE_32V

led1 = digitalio.DigitalInOut(board.D13)     #1
led1.direction = digitalio.Direction.OUTPUT

led2 = digitalio.DigitalInOut(board.D19)     #2
led2.direction = digitalio.Direction.OUTPUT

led3 = digitalio.DigitalInOut(board.D26)     #3
led3.direction = digitalio.Direction.OUTPUT

BATT_SYS = digitalio.DigitalInOut(board.D4)     
BATT_SYS.direction = digitalio.Direction.OUTPUT

def ahora():
    ahora_time = datetime.datetime.now()
    ahora_hora = ahora_time.hour
    ahora_minuto = ahora_time.minute
    ahora_segundo = ahora_time.second
    ahora_ya = ahora_hora + (ahora_minuto/60) + (ahora_segundo/3600)
    return ahora_ya

def HR_OSC():                               #Obtener el Flag "HR" del OSC
    # Hora de Interés 10:45 AM a 2:45 PM
    inicio_ventana_interes = 8 + 45/60     # Check WeatherUnderground
    fin_ventana_interes = 16 + 45/60        # Check WeatherUnderground
    # Pedir el tiempo actual
    now_osc = round(ahora(),4)
    
    if (now_osc > inicio_ventana_interes) and (now_osc < fin_ventana_interes):
        HR = 1
    else:
        HR = 0
    return HR


def ask_power_grid_dc():
    bus_voltage_1 = ina2191.bus_voltage
    current_1 = ina2191.current
    power1 = bus_voltage_1 * (current_1 / 1000)  # power in watts
    time.sleep(0.5)
    bus_voltage_2 = ina2192.bus_voltage
    current_2 = ina2192.current
    power2 = bus_voltage_2 * (current_2 / 1000)  # power in watts
    time.sleep(0.5)
    power_combo1 = power1 + power2
            
    bus_voltage_3 = ina2193.bus_voltage
    current_3 = ina2193.current
    power3 = bus_voltage_3 * (current_3 / 1000)  # power in watts
    time.sleep(0.5)
    bus_voltage_4 = ina2194.bus_voltage
    current_4 = ina2194.current
    power4 = bus_voltage_4 * (current_4 / 1000)  # power in watts
    time.sleep(0.5)
    power_combo2 = power3 + power4

    power_grid = power_combo1 + power_combo2
    return power_grid

def ask_power_wt():
    bus_voltage_5 = ina2195.bus_voltage
    current_5 = ina2195.current
    power_wt = bus_voltage_5 * (current_5 / 1000)  # power in watts
    time.sleep(0.5)
    power_wt_adj = power_wt + 4.5
    if power_wt_adj < 4.51:
        power_wt_adj = 0
    return power_wt_adj 

def ask_power_sp():
    current_sp = ina2601.current / 1000
    power_sp = ina2601.voltage * current_sp  # power in watts
    time.sleep(0.5)
    return power_sp

def ask_power_load():
    current_load = ina2603.current / 1000
    power_load = ina2603.voltage * current_load  # power in watts
    time.sleep(0.5)
    return power_load

def ask_power_batt():
    current_batt = ina2602.current / 1000
    power_batt = ina2602.voltage * current_batt  # power in watts
    time.sleep(0.5)
    return power_batt

def BS_bypass():
    current_batt_bp = ina2602.current / 1000
    voltage_batt_bp = ina2602.voltage
    power_batt = voltage_batt_bp * current_batt_bp  # power in watts
    print(voltage_batt_bp)
    print(current_batt_bp)
    if voltage_batt_bp > 12.5:
        bs_choice = True
    else:
        bs_choice = False
    time.sleep(0.5)
    return bs_choice

# Controlador Fuzzy para el DCDC del Panel
# New Antecedent/Consequent objects hold universe variables and membership functions
power_offset = ctrl.Antecedent(np.arange(-15, 15, 0.1), 'power_offset')
dcdc_offset = ctrl.Consequent(np.arange(-10, 10, 0.1), 'dcdc_offset')
# Auto-membership function population is possible with .automf(3, 5, or 7)
power_offset.automf(5)
# Custom membership functions can be built interactively with a familiar,
# Pythonic API
dcdc_offset['really low'] = fuzz.trimf(dcdc_offset.universe, [-15, -15, -5])
dcdc_offset['low'] = fuzz.trimf(dcdc_offset.universe, [-15, -5, 0])
dcdc_offset['fair'] = fuzz.trimf(dcdc_offset.universe, [-1, 0, 1])
dcdc_offset['high'] = fuzz.trimf(dcdc_offset.universe, [0, 5, 15])
dcdc_offset['really high'] = fuzz.trimf(dcdc_offset.universe, [5, 15, 15])

rule1 = ctrl.Rule(power_offset['poor'], dcdc_offset['really low'])
rule2 = ctrl.Rule(power_offset['mediocre'], dcdc_offset['low'])
rule3 = ctrl.Rule(power_offset['average'], dcdc_offset['fair'])
rule4 = ctrl.Rule(power_offset['decent'], dcdc_offset['high'])
rule5 = ctrl.Rule(power_offset['good'], dcdc_offset['really high'])

setting_ctrl = ctrl.ControlSystem([rule1,rule2, rule3, rule4, rule5])
setting = ctrl.ControlSystemSimulation(setting_ctrl)

epsilon = 0.1
adj_dac = 1.6
power_fz = []
power_fz.append(0)
power_fz.append(0)

delta_power_fz = []
delta_power_fz.append(0)
delta_power_fz.append(0)

#Configuración del Cliente ModBus para el PM800
def ask_ac():
    intento=True
    client = ModbusClient(method='rtu', port= '/dev/ttyUSB1', bytesize=8, timeout=1, baudrate= 19200)    
    while intento:
        try :
            result1 = client.read_holding_registers(11729, 2, unit=1)# Power A
            result2 = client.read_holding_registers(11753, 2, unit=1)# Power Factor A
            decoder1 = BinaryPayloadDecoder.fromRegisters(result1.registers, byteorder=Endian.Big )
            PTred = decoder1.decode_32bit_float()
            PTred = round(PTred,3)
            decoder2 = BinaryPayloadDecoder.fromRegisters(result2.registers, byteorder=Endian.Big )
            FPred = decoder2.decode_32bit_float()
            FPred = round(FPred,3)   
            intento=False
        except AttributeError:
            PTred = 0
            FPred = 0
            intento=False
        except:
            client = ModbusClient(method='rtu', port= '/dev/ttyUSB0', bytesize=8, timeout=1, baudrate= 19200)
            
    print("Power Grid AC : {:6.3f}   W".format(PTred))
    print("Power Factor : {:6.3f}     ".format(FPred))
    time.sleep(0.5)
    return

#print('Ingrese porcentaje DAC entre 0% y 100%')
#x_dac = float(input())
x1dcdc = 80     # DCDC Setting inicial
y_dac = -0.013*x1dcdc + 61.8
y_dac= y_dac+adj_dac   #ajuste

fuzzy_bp = HR_OSC()
if fuzzy_bp == 1:
    y_dac = y_dac
else:
    y_dac = 10
    
y_dac = y_dac/100

dac_setpoint.normalized_value = y_dac
time.sleep (0.5)

y1dcdc = ask_power_grid_dc()
#print("Power Grid DC : {:6.3f}   W".format(y1dcdc))

power_fz.append(y1dcdc)
power_fz.pop(0)

zdcdc = 10
y_dac = -0.013*zdcdc + 61.8
y_dac= y_dac+adj_dac   #ajuste

fuzzy_bp = HR_OSC()
if fuzzy_bp == 1:
    y_dac = y_dac
else:
    y_dac = 10

y_dac = y_dac/100

dac_setpoint.normalized_value = y_dac
time.sleep (0.5)

if x1dcdc >= zdcdc:
    a = -1
else:
    a = 1

new_power_dcdc = ask_power_grid_dc()
#print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
            
#print('Prueba Battery System Bypass...')
#print('Bypass SI = 1')
#print('Bypass NO = 0')
#print('Bypass el Battery System? ')
#bs_input = int(input())

flag_error = 0
x = 1

bs_input = 0


if bs_input==1:
    BATT_SYS.value = True
elif bs_input==0:
    BATT_SYS.value = False
else:
    BATT_SYS.value = False
try:
    fecha_inicial = datetime.datetime.now()
    fecha_actual=datetime.datetime.now()
    fecha_corte= fecha_inicial + datetime.timedelta(hours=1)
    print("La fecha y hora de inicio es : ",fecha_inicial)
    total_load=0
    consumo_mes_anterior=0
    while True:
        
        if flag_error == 0:
            print('Ingrese el estado del sistema:')
            x = int(input())
            
        try:    
            while True:

                if fecha_actual >= fecha_corte:
                    fecha_inicial= datetime.datetime.now()
                    fecha_corte= fecha_inicial + datetime.timedelta(hours=1)
                    print("La fecha y hora de inicio es : ",fecha_inicial)
                    consumo_mes_anterior=total_load
                    total_load=0

                #flag_error = 1
                if x==1:
                    led1.value = False
                    led2.value = False
                    led3.value = False
                    #print('Fuzzy ON')
                    #print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
    
                    power_fz.append(new_power_dcdc)
                    power_fz.pop(0)
                    delta_power_fz.append(power_fz[1] - power_fz[0])
                    delta_power_fz.pop(0)
                    #print('la diferencia en potencia es :  ')
                    #print(power_fz[1] - power_fz[0],'W')
                    #print(' ')
    
                    if (abs(power_fz[1] - power_fz[0])) < epsilon:
                        #print('El offset resultante es... ')
                        dcdc_to_affect = 0
                        #print(dcdc_to_affect)
                        #print('')
                        #print('El DCDC Setting que debe enviarse es...')
                        z1dcdc = zdcdc + dcdc_to_affect
                        zdcdc=z1dcdc
                        #print(zdcdc)
                        #print(' ')
                        if zdcdc < 1:
                            zdcdc = 1
                        if zdcdc > 99:
                            zdcdc = 99
                        #print(zdcdc)
                        #print(' ')
                        y_dac = -0.013*zdcdc + 61.8
                        y_dac= y_dac+adj_dac   #ajuste
                        fuzzy_bp = HR_OSC()
                        if fuzzy_bp == 1:
                            y_dac = y_dac
                        else:
                            y_dac = 10
                        y_dac = y_dac/100
                        dac_setpoint.normalized_value = y_dac
                        time.sleep (0.5)
                        new_power_dcdc = ask_power_grid_dc()
                        wt_power = ask_power_wt()
                        ask_ac()
                        solar_panel_pow = ask_power_sp()
                        battery_pow = ask_power_batt()
                        load_pow=ask_power_load()
                        total_load=total_load+load_pow*2
                        fecha_actual=datetime.datetime.now()
                        ventana_tiempo=fecha_actual-fecha_inicial
                        print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
                        print("Power WT : {:6.3f}   W".format(wt_power))
                        print("Power SP : {:6.3f}   W".format(solar_panel_pow))
                        print("Power BATT : {:6.3f}   W".format(battery_pow))
                        print("Power LOAD : {:6.3f}   W".format(load_pow))
                        print("Total LOAD :", total_load, " W", " en", ventana_tiempo)
                        print("El consumo en la hora anterior fue de: ",consumo_mes_anterior)
                        print(' ')
                        BATT_SYS.value = BS_bypass()
                    else:
                        setting.input['power_offset'] = power_fz[1] - power_fz[0]
                        # Crunch the numbers
                        setting.compute()

                        #print('El offset resultante es... ')
                        dcdc_to_affect = setting.output['dcdc_offset']

                        if a == -1:
                            dcdc_to_affect = 1*(dcdc_to_affect)
                        else:
                            dcdc_to_affect = -1*(dcdc_to_affect)

                        #print(dcdc_to_affect)
                        #print(' ')
                        #print('El DCDC Setting que debe enviarse es...')
                        z1dcdc = zdcdc + dcdc_to_affect
                        zdcdc=z1dcdc
                        if zdcdc < 1:
                            zdcdc = 1
                        if zdcdc > 99:
                            zdcdc = 99
                        #print(zdcdc)
                        #print(' ')
                        y_dac = -0.013*zdcdc + 61.8
                        y_dac= y_dac+adj_dac   #ajuste
                        fuzzy_bp = HR_OSC()
                        if fuzzy_bp == 1:
                            y_dac = y_dac
                        else:
                            y_dac = 10
                        y_dac = y_dac/100
                        dac_setpoint.normalized_value = y_dac
                        new_power_dcdc = ask_power_grid_dc()
                        wt_power = ask_power_wt()
                        ask_ac()
                        solar_panel_pow = ask_power_sp()
                        battery_pow = ask_power_batt()
                        load_pow=ask_power_load()
                        total_load=total_load+load_pow*2
                        fecha_actual=datetime.datetime.now()
                        ventana_tiempo=fecha_actual-fecha_inicial
                        print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
                        print("Power WT : {:6.3f}   W".format(wt_power))
                        print("Power SP : {:6.3f}   W".format(solar_panel_pow))
                        print("Power BATT : {:6.3f}   W".format(battery_pow))
                        print("Power LOAD : {:6.3f}   W".format(load_pow))
                        print("Total LOAD :", total_load, " W", " en", ventana_tiempo)
                        print("El consumo en la hora anterior fue de: ",consumo_mes_anterior)
                        print(' ')                    
                        BATT_SYS.value = BS_bypass()
                        if dcdc_to_affect < 0:
                            a = -1
                        else:
                            a = 1
            
                elif x==2:
                    led1.value = False
                    led2.value = False
                    led3.value = True
                    dac_setpoint.normalized_value = 0.9
                    time.sleep (0.5)
                    new_power_dcdc = ask_power_grid_dc()
                    wt_power = ask_power_wt()
                    time.sleep(2)
                    ask_ac()
                    solar_panel_pow = ask_power_sp()
                    battery_pow = ask_power_batt()
                    load_pow=ask_power_load()
                    total_load=total_load+load_pow*2
                    fecha_actual=datetime.datetime.now()
                    ventana_tiempo=fecha_actual-fecha_inicial
                    print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
                    print("Power WT : {:6.3f}   W".format(wt_power))
                    print("Power SP : {:6.3f}   W".format(solar_panel_pow))
                    print("Power BATT : {:6.3f}   W".format(battery_pow))
                    print("Power LOAD : {:6.3f}   W".format(load_pow))
                    print("Total LOAD :", total_load, " W", " en", ventana_tiempo)
                    print("El consumo en la hora anterior fue de: ",consumo_mes_anterior)
                    print(' ')
                    BATT_SYS.value = BS_bypass()
                    
                elif x==3:
                    led1.value = False
                    led2.value = True
                    led3.value = False
                    dac_setpoint.normalized_value = 0.9
                    time.sleep (0.5)
                    new_power_dcdc = ask_power_grid_dc()
                    wt_power = ask_power_wt()
                    time.sleep(2)
                    ask_ac()
                    solar_panel_pow = ask_power_sp()
                    battery_pow = ask_power_batt()
                    load_pow=ask_power_load()
                    total_load=total_load+load_pow*2
                    fecha_actual=datetime.datetime.now()
                    ventana_tiempo=fecha_actual-fecha_inicial
                    print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
                    print("Power WT : {:6.3f}   W".format(wt_power))
                    print("Power SP : {:6.3f}   W".format(solar_panel_pow))
                    print("Power BATT : {:6.3f}   W".format(battery_pow))
                    print("Power LOAD : {:6.3f}   W".format(load_pow))
                    print("Total LOAD :", total_load, " W", " en", ventana_tiempo)
                    print("El consumo en la hora anterior fue de: ",consumo_mes_anterior)
                    print(' ')
                    BATT_SYS.value = BS_bypass()
                    
                elif x==4:
                    led1.value = False
                    led2.value = True
                    led3.value = True
                    dac_setpoint.normalized_value = 0.9
                    time.sleep (0.5)
                    new_power_dcdc = ask_power_grid_dc()
                    wt_power = ask_power_wt()
                    time.sleep(2)
                    ask_ac()
                    solar_panel_pow = ask_power_sp()
                    battery_pow = ask_power_batt()
                    load_pow=ask_power_load()
                    total_load=total_load+load_pow*2
                    fecha_actual=datetime.datetime.now()
                    ventana_tiempo=fecha_actual-fecha_inicial
                    print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
                    print("Power WT : {:6.3f}   W".format(wt_power))
                    print("Power SP : {:6.3f}   W".format(solar_panel_pow))
                    print("Power BATT : {:6.3f}   W".format(battery_pow))
                    print("Power LOAD : {:6.3f}   W".format(load_pow))
                    print("Total LOAD :", total_load, " W", " en", ventana_tiempo)
                    print("El consumo en la hora anterior fue de: ",consumo_mes_anterior)
                    print(' ')
                    BATT_SYS.value = BS_bypass()
                    
                elif x==5:
                    led1.value = True
                    led2.value = False
                    led3.value = False
                    dac_setpoint.normalized_value = 0.9
                    time.sleep (0.5)
                    new_power_dcdc = ask_power_grid_dc()
                    wt_power = ask_power_wt()
                    time.sleep(2)
                    ask_ac()
                    solar_panel_pow = ask_power_sp()
                    battery_pow = ask_power_batt()
                    load_pow=ask_power_load()
                    total_load=total_load+load_pow*2
                    fecha_actual=datetime.datetime.now()
                    ventana_tiempo=fecha_actual-fecha_inicial
                    print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
                    print("Power WT : {:6.3f}   W".format(wt_power))
                    print("Power SP : {:6.3f}   W".format(solar_panel_pow))
                    print("Power BATT : {:6.3f}   W".format(battery_pow))
                    print("Power LOAD : {:6.3f}   W".format(load_pow))
                    print("Total LOAD :", total_load, " W", " en", ventana_tiempo)
                    print("El consumo en la hora anterior fue de: ",consumo_mes_anterior)
                    print(' ')
                    BATT_SYS.value = BS_bypass()
                    
                else:
                    led1.value = False
                    led2.value = False
                    led3.value = False
                    dac_setpoint.normalized_value = 0.9
                    time.sleep (0.5)
                    new_power_dcdc = ask_power_grid_dc()
                    wt_power = ask_power_wt()
                    time.sleep(2)
                    ask_ac()
                    psolar_panel_pow = ask_power_sp()
                    battery_pow = ask_power_batt()
                    load_pow=ask_power_load()
                    print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
                    print("Power WT : {:6.3f}   W".format(wt_power))
                    print("Power SP : {:6.3f}   W".format(solar_panel_pow))
                    print("Power BATT : {:6.3f}   W".format(battery_pow))
                    print("Power LOAD : {:6.3f}   W".format(load_pow))
                    print(' ')
                    BATT_SYS.value = BS_bypass()
                
                time.sleep(1)
                
        
        except IOError:
            flag_error = 1
            pass
        except KeyboardInterrupt:
            flag_error = 0
            pass
        except OSError:
            flag_error = 1
            pass
        else:
            flag_error = 1
            pass
               
except KeyboardInterrupt:
    pass
