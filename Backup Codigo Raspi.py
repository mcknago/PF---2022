import os
import time
import datetime
import threading
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
    if voltage_batt_bp > 12.5:
        bs_choice = True #  Bypass
    else:
        bs_choice = False # Normal
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
servicio=True
tiempo_sin_servicio = inicio_apagon = fin_apagon=datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
def ask_ac():
    global servicio, tiempo_sin_servicio, inicio_apagon, fin_apagon
    intento=True
    client = ModbusClient(method='rtu', port= '/dev/ttyUSB1', bytesize=8, timeout=1, baudrate= 19200)    
    while intento:
        try :
            #Para calcular el tiempo de apagones
            result1 = client.read_holding_registers(11729, 2, unit=1)# Power A
            result2 = client.read_holding_registers(11753, 2, unit=1)# Power Factor A
            decoder1 = BinaryPayloadDecoder.fromRegisters(result1.registers, byteorder=Endian.Big )
            PTred = decoder1.decode_32bit_float()
            PTred = round(PTred,3)
            decoder2 = BinaryPayloadDecoder.fromRegisters(result2.registers, byteorder=Endian.Big )
            FPred = decoder2.decode_32bit_float()
            FPred = round(FPred,3)   
            intento=False
            
            if servicio==False:
                fin_apagon=datetime.datetime.now()
                tiempo_apagon=fin_apagon-inicio_apagon
                tiempo_sin_servicio=tiempo_sin_servicio+tiempo_apagon
                print('El tiempo sin servicio ha sido de: ',tiempo_sin_servicio)
                tiempo_apagon = inicio_apagon = fin_apagon=datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
                servicio=True
            
        except AttributeError:
            if servicio==True:
                inicio_apagon=datetime.datetime.now()
                servicio=False
            PTred = 0
            FPred = 0
            intento=False
        except:
            client = ModbusClient(method='rtu', port= '/dev/ttyUSB0', bytesize=8, timeout=1, baudrate= 19200)
            
    time.sleep(0.5)
    return (PTred,FPred)

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
S = 1

bs_input = 0
################################### INICIO CONTROLADOR ###################################
def Controlador():
    global S, battery_pow, PTred
    estado_nuevo.set()
    estado_probado.clear()

    if bs_input==1:
        BATT_SYS.value = True
    elif bs_input==0:
        BATT_SYS.value = False
    else:
        BATT_SYS.value = False
    try:
        fecha_inicial = datetime.datetime.now()
        fecha_actual=datetime.datetime.now()
        tiempo_anterior=fecha_actual
        fecha_corte= fecha_inicial + datetime.timedelta(hours=12)
        consumo_mes_anterior=0
        print("La fecha y hora de inicio es : ",fecha_inicial)
        precio_kwh= 573.240
        total_load=0
        total_load_con_sistema=0
        i=0
        power_delta=0
        power_delta_con_sistema=0
        time_delta=0  
        power_load_promedio=0 
        eficiencia_dcac=0.85
        n=5 #Numero de muestras de potencia

        while True:
            
            if flag_error == 0:
                x=S
                print(f'Controlador : Me encuentro en estado {x} ...')
                
            try:    
                while True:

                    if fecha_actual >= fecha_corte:
                        fecha_inicial= datetime.datetime.now()
                        fecha_corte= fecha_inicial + datetime.timedelta(hours=12)
                        print("La fecha y hora de inicio es : ",fecha_inicial)
                        tiempo_sin_servicio=datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
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
                            solar_panel_pow = ask_power_sp()
                            battery_pow = ask_power_batt()
                            load_pow=ask_power_load()
                            (PTred,FPred)=ask_ac()
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
                            solar_panel_pow = ask_power_sp()
                            battery_pow = ask_power_batt()
                            load_pow=ask_power_load()
                            (PTred,FPred)=ask_ac()                   
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
                        solar_panel_pow = ask_power_sp()
                        battery_pow = ask_power_batt()
                        load_pow=ask_power_load()
                        (PTred,FPred)=ask_ac()
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
                        solar_panel_pow = ask_power_sp()
                        battery_pow = ask_power_batt()
                        load_pow=ask_power_load()
                        (PTred,FPred)=ask_ac()
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
                        solar_panel_pow = ask_power_sp()
                        battery_pow = ask_power_batt()
                        (PTred,FPred)=ask_ac()
                        load_pow=ask_power_load() + PTred
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
                        solar_panel_pow = ask_power_sp()
                        battery_pow = ask_power_batt()
                        load_pow=ask_power_load()
                        (PTred,FPred)=ask_ac()
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
                        psolar_panel_pow = ask_power_sp()
                        battery_pow = ask_power_batt()
                        load_pow=ask_power_load()
                        (PTred,FPred)=ask_ac()
                        BATT_SYS.value = BS_bypass()
                    
                    #print("Power Grid AC : {:6.3f}   W".format(PTred))
                    #print("Power Grid FP : {:6.3f}   W".format(FPred))
                    #print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
                    #print("Power WT : {:6.3f}   W".format(wt_power))
                    #print("Power SP : {:6.3f}   W".format(solar_panel_pow))
                    #print("Power BATT : {:6.3f}   W".format(battery_pow))
                    #print("Power LOAD : {:6.3f}   W".format(load_pow))
                    #print(' ')
    #Calculo de la potencia 
                    fecha_actual=datetime.datetime.now()
                    tiempo_subdelta=fecha_actual-tiempo_anterior
                    time_delta=time_delta+int(tiempo_subdelta.total_seconds())                
                    power_delta=power_delta+load_pow*eficiencia_dcac
                    power_delta_con_sistema=power_delta_con_sistema + PTred
                    tiempo_anterior=fecha_actual     
                    i=i+1    
                    if i>=n:
                        total_load=total_load+(((power_delta/n)*time_delta)/3600)/1000
                        total_load_con_sistema=total_load_con_sistema+(((power_delta_con_sistema/n)*time_delta)/3600)/1000
                        ventana_tiempo=fecha_actual-fecha_inicial
                        factura_sin_sistema=total_load*precio_kwh
                        factura_con_sistema = total_load_con_sistema*precio_kwh
                    #    print("Total LOAD :", total_load, " kW*h", " en", ventana_tiempo) # Falta multiplicar por eficiencia del inversor
                    #    print("El consumo en el dia anterior fue de: ",consumo_mes_anterior,' w*h')
                    #    print("La factura sin el sistema es de : $",factura_sin_sistema)
                    #    print("La factura con el sistema es de : $",factura_con_sistema)
                    #    print(' ')
                        i=0
                        time_delta=0
                        power_delta=0
                        power_delta_con_sistema=0

                    print(f'Controlador : En estado {x} La potencia del Grid es de {PTred} y la potencia de la bateria es de {battery_pow} ...')
                    if estado_nuevo.is_set and not(estado_probado.is_set()):
                        estado_nuevo.clear()
                        estado_probado.set()
                        estado_nuevo.wait()
                    
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

################################### INICIO Arbol de Decisión ###################################
def Arbol_decision():
    global S, battery_pow, PTred

    def ahora():
        ahora_time = datetime.datetime.now()
        ahora_hora = ahora_time.hour
        ahora_minuto = ahora_time.minute
        ahora_segundo = ahora_time.second
        ahora_ya = ahora_hora + (ahora_minuto/60) + (ahora_segundo/3600)
        return ahora_ya

    def HR_OSC():                               #Obtener el Flag "HR" del OSC
        # Hora de Interés 10:45 AM a 2:45 PM
        inicio_ventana_interes = 7 + 45/60     # Check WeatherUnderground
        fin_ventana_interes = 14 + 45/60        # Check WeatherUnderground
        # Pedir el tiempo actual
        now_osc = round(ahora(),4)
        
        if (now_osc > inicio_ventana_interes) and (now_osc < fin_ventana_interes):
            HR = 1
        else:
            HR = 0
        return HR

    def BATT_OSC(BATT_POW):                     # Obtener el Flag "BATT" del OSC
        if BATT_POW >= 5:                        # Maxima potencia seleccionada
            BATT = 1
        else:
            BATT = 0
        return BATT

    def VAC_OSC(VAC_V):                              #Obtener el Flag "VAC" del OSC
        if VAC_V > 100:
            VAC = 1
        else:
            VAC = 0
        return VAC        

    def S_1():
        global PTred, battery_pow, S
        VAC_OS_F = VAC_OSC(PTred)
        if VAC_OS_F == 0:
            S = 3
            time.sleep(2)
            BATT_OS_F = BATT_OSC(battery_pow)
            if BATT_OS_F == 1:
                S = 3
                time.sleep(2)
            else:
                S = 1
                time.sleep(2)
                BATT_OS_F = BATT_OSC(battery_pow)
                if BATT_OS_F == 1:
                    S = 3
                    time.sleep(2)
                else:
                    if HR_OS == 1:
                        S = 2
                        time.sleep(2)
                        BATT_OS_F = BATT_OSC(battery_pow)
                        if BATT_OS_F == 0:
                            S = 2
                        else:
                            S = 1
                            time.sleep(2)
                    else:
                        S = 1
                        time.sleep(2)

        else:
            if HR_OS == 1:
                S = 2
                time.sleep(2)
                BATT_OS_F = BATT_OSC(battery_pow)
                if BATT_OS_F == 1:
                    S = 1
                    time.sleep(2)
                    BATT_OS_F = BATT_OSC(battery_pow)
                    if BATT_OS_F == 1:
                        S = 1
                    else:
                        S = 4
                        time.sleep(2)
                        BATT_OS_F = BATT_OSC(battery_pow)
                        if BATT_OS_F == 1:
                            S = 1
                            time.sleep(2)
                        else:
                            S = 4
                else:
                    S = 2
            else:
                S = 4
                time.sleep(2)
                BATT_OS_F = BATT_OSC(battery_pow)
                if BATT_OS_F == 1:
                    S = 1
                    time.sleep(2)
                else:
                    S = 4
                    
        return S

        
    BATT_F = battery_pow

    VAC_F = PTred
            
    HR_OS = HR_OSC()
    BATT_OS = BATT_OSC(BATT_F)
    VAC_OS = VAC_OSC(VAC_F)

    #print(HR_OS)
    #print(BATT_OS)
    #print(VAC_OS)
    #print('   ')

    #Empecemos pidiendo el tiempo actual...
    dale = ahora()

    # vamos a utilizar un tiempo de chequeo de X minutos
    chequeo = 1/60

    # Estado de inicio por defecto es S1
    S = 1

    while True:
        while (ahora() < dale + chequeo):
            if S == 1:
                S = S_1()
            elif S == 2:
                BATT_OS = battery_pow
                if BATT_OS == 1:
                    S = 1
                else:
                    S = 2
            elif S == 3:
                BATT_OS = battery_pow
                if BATT_OS == 1:
                    S = 3
                else:
                    S = 1
            else:
                BATT_OS = battery_pow
                if BATT_OS == 1:
                    S = 1
                else:
                    S = 4

            print('    ')
            print('El estado del sistema es...     ')
            print(S)
            print('    ')
            print('Waiting...     ')
            print('    ')
            time.sleep(2*60)
            
        dale = ahora()



estado_nuevo = threading.Event() #Le dice al controlador qué debe hacer
estado_probado = threading.Event() #Le dice al arbol qué debe hacer

thread_control = threading.Thread(target=Controlador)
thread_arbol = threading.Thread(target=Arbol_decision)

thread_control.start()
thread_arbol.start()
