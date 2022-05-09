import os
import time
import datetime
import threading
import board
import digitalio
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219
#from mcp3008 import MCP3008
import adafruit_mcp4725
import adafruit_ina260

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

from tkinter import *
from PIL import Image,ImageTk

import psutil


precio_kwh= 573.240    
state_controler=1

################################### INICIO CONTROLADOR ###################################
def Controlador():
    global state_controler,servicio, inicio_apagon, fin_apagon, logo_lb_Flecha_Bateria_UP, logo_lb_Flecha_Bateria_D,precio_kwh,sin_sistema_controler,tiempo_sin_servicio_controler,state_provisional,intentos_comu_arbol
    global wt_power_controler,panel_power_controler,PTred_controler,FPred_controler,load_pow_controler,battery_pow_controler,mes_actual_controler,mes_anterior_controler,con_sistema_controler,P_bateria_decision
    servicio=True
    intentos_comu_arbol=P_bateria_decision=0
    con_sistema_controler=sin_sistema_controler=0
    tiempo_sin_servicio_controler = inicio_apagon = fin_apagon=datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
    nuevas_variables_controlador.clear()    #No se han actualizado las variables
    estado_nuevo.set()
    estado_probado.clear()
    i2c_bus = board.I2C()
    intento=True
    while intento:
        try:
            #ina2191 = INA219(i2c_bus, 0x40)
            ina2195 = INA219(i2c_bus, 0x42)
            #ina2192 = INA219(i2c_bus, 0x44)
            #ina2193 = INA219(i2c_bus, 0x41)
            #ina2194 = INA219(i2c_bus, 0x45)
            ina2601 = adafruit_ina260.INA260(i2c_bus, 0x43)
            ina2602 = adafruit_ina260.INA260(i2c_bus, 0x46)
            ina2603 = adafruit_ina260.INA260(i2c_bus, 0x47)
            dac_setpoint = adafruit_mcp4725.MCP4725(i2c_bus, address=0x61)
            # Configuration to use 32 samples averaging for both bus voltage and shunt voltage
            #ina2191.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            #ina2191.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            #ina2192.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            #ina2192.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            #ina2193.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            #ina2193.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            #ina2194.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            #ina2194.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            ina2195.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            ina2195.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
            # Change voltage range to 32V
            #ina2191.bus_voltage_range = BusVoltageRange.RANGE_32V
            #ina2192.bus_voltage_range = BusVoltageRange.RANGE_32V
            #ina2193.bus_voltage_range = BusVoltageRange.RANGE_32V
            #ina2194.bus_voltage_range = BusVoltageRange.RANGE_32V
            ina2195.bus_voltage_range = BusVoltageRange.RANGE_32V

            led1 = digitalio.DigitalInOut(board.D13)     #1
            led1.direction = digitalio.Direction.OUTPUT

            led2 = digitalio.DigitalInOut(board.D19)     #2
            led2.direction = digitalio.Direction.OUTPUT

            led3 = digitalio.DigitalInOut(board.D26)     #3
            led3.direction = digitalio.Direction.OUTPUT

            BATT_SYS = digitalio.DigitalInOut(board.D4)     
            BATT_SYS.direction = digitalio.Direction.OUTPUT
            intento = False
        except:
            print('Se descalibraron los sensores...Dormiré 15 segundos...')
            time.sleep(30)
            

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
    def ask_ac():
        global servicio, tiempo_sin_servicio_controler, inicio_apagon, fin_apagon
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
                    tiempo_sin_servicio_controler=tiempo_sin_servicio_controler+tiempo_apagon
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

    def comunicar_arbol():
        global intentos_comu_arbol,P_bateria_decision,battery_pow_controler
        intentos_comu_arbol=intentos_comu_arbol+1
        P_bateria_decision=P_bateria_decision+battery_pow_controler
        if estado_nuevo.is_set and not(estado_probado.is_set()) and state_provisional==state_controler and intentos_comu_arbol>=3:
            estado_nuevo.clear()
            estado_probado.set()
            estado_nuevo.wait()
            P_bateria_decision=P_bateria_decision/3
            intentos_comu_arbol=0         
        nuevas_variables_controlador.set()
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

    #y1dcdc = ask_power_grid_dc()
    #print("Power Grid DC : {:6.3f}   W".format(y1dcdc))
    (PTred_controler,FPred_controler)=ask_ac()  
    y1dcdc =  PTred_controler*0.8 #MIENTRAS SE COMPRAN LOS SENSORES
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

    #new_power_dcdc = ask_power_grid_dc()
    (PTred_controler,FPred_controler)=ask_ac()  
    new_power_dcdc =  PTred_controler*0.8 #MIENTRAS SE COMPRAN LOS SENSORES
    #print("Power Grid DC : {:6.3f}   W".format(new_power_dcdc))
                
    #print('Prueba Battery System Bypass...')
    #print('Bypass SI = 1')
    #print('Bypass NO = 0')
    #print('Bypass el Battery System? ')
    #bs_input = int(input())

    flag_error = 0
    state_controler = 1

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
        tiempo_anterior=fecha_actual
        fecha_corte= fecha_inicial + datetime.timedelta(hours=12)
        mes_anterior_controler=0
        print("La fecha y hora de inicio es : ",fecha_inicial)
        total_load=mes_actual_controler=i=power_delta=power_delta_con_sistema=time_delta=0
        eficiencia_dcac=0.85
        n=5 #Numero de muestras de potencia
        while True:
            try:    
                while True:
                    state_provisional=state_controler
                    if fecha_actual >= fecha_corte:
                        fecha_inicial= datetime.datetime.now()
                        fecha_corte= fecha_inicial + datetime.timedelta(hours=12)
                        print("Controlador: La fecha y hora de inicio es : ",fecha_inicial)
                        tiempo_sin_servicio_controler=datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
                        mes_anterior_controler=total_load
                        total_load=0

                    #flag_error = 1
                    if state_provisional==1:
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
                            #new_power_dcdc = ask_power_grid_dc()
                            wt_power_controler = ask_power_wt()
                            panel_power_controler = ask_power_sp()
                            battery_pow_controler = ask_power_batt()
                            load_pow_controler=ask_power_load()
                            (PTred_controler,FPred_controler)=ask_ac()
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
                            #new_power_dcdc = ask_power_grid_dc()
                            wt_power_controler = ask_power_wt()
                            panel_power_controler = ask_power_sp()
                            battery_pow_controler = ask_power_batt()
                            load_pow_controler=ask_power_load()
                            (PTred_controler,FPred_controler)=ask_ac()                   
                            BATT_SYS.value = BS_bypass()
                            if dcdc_to_affect < 0:
                                a = -1
                            else:
                                a = 1
                
                    elif state_provisional==2:
                        led1.value = False
                        led2.value = False
                        led3.value = True
                        dac_setpoint.normalized_value = 0.9
                        time.sleep (0.5)
                        #new_power_dcdc = ask_power_grid_dc()
                        wt_power_controler = ask_power_wt()
                        time.sleep(2)
                        panel_power_controler = ask_power_sp()
                        battery_pow_controler = ask_power_batt()
                        load_pow_controler=ask_power_load()
                        (PTred_controler,FPred_controler)=ask_ac()
                        BATT_SYS.value = BS_bypass()
                        
                    elif state_provisional==3:
                        led1.value = False
                        led2.value = True
                        led3.value = False
                        dac_setpoint.normalized_value = 0.9
                        time.sleep (0.5)
                        #new_power_dcdc = ask_power_grid_dc()
                        wt_power_controler = ask_power_wt()
                        time.sleep(2)
                        panel_power_controler = ask_power_sp()
                        battery_pow_controler = ask_power_batt()
                        load_pow_controler=ask_power_load()
                        (PTred_controler,FPred_controler)=ask_ac()
                        BATT_SYS.value = BS_bypass()
                        
                    elif state_provisional==4:
                        led1.value = False
                        led2.value = True
                        led3.value = True
                        dac_setpoint.normalized_value = 0.9
                        time.sleep (0.5)
                        #new_power_dcdc = ask_power_grid_dc()
                        wt_power_controler = ask_power_wt()
                        time.sleep(2)
                        panel_power_controler = ask_power_sp()
                        battery_pow_controler = ask_power_batt()
                        (PTred_controler,FPred_controler)=ask_ac()
                        load_pow_controler=ask_power_load() + PTred_controler
                        BATT_SYS.value = BS_bypass()
                        
                    elif state_provisional==5:
                        led1.value = True
                        led2.value = False
                        led3.value = False
                        dac_setpoint.normalized_value = 0.9
                        time.sleep (0.5)
                        #new_power_dcdc = ask_power_grid_dc()
                        wt_power_controler = ask_power_wt()
                        time.sleep(2)
                        panel_power_controler = ask_power_sp()
                        battery_pow_controler = ask_power_batt()
                        load_pow_controler=ask_power_load()
                        (PTred_controler,FPred_controler)=ask_ac()
                        BATT_SYS.value = BS_bypass()
                        
                    else:
                        led1.value = False
                        led2.value = False
                        led3.value = False
                        dac_setpoint.normalized_value = 0.9
                        time.sleep (0.5)
                        #new_power_dcdc = ask_power_grid_dc()
                        wt_power_controler = ask_power_wt()
                        time.sleep(2)
                        panel_power_controler = ask_power_sp()
                        battery_pow_controler = ask_power_batt()
                        load_pow_controler=ask_power_load()
                        (PTred_controler,FPred_controler)=ask_ac()
                        BATT_SYS.value = BS_bypass()
                    print("Potencia de la Carga: ",battery_pow_controler)
                    #Se actualizaron las variables

    #Calculo de la potencia 
                    fecha_actual=datetime.datetime.now()
                    tiempo_subdelta=fecha_actual-tiempo_anterior
                    time_delta=time_delta+int(tiempo_subdelta.total_seconds())                
                    power_delta=power_delta+load_pow_controler*eficiencia_dcac
                    power_delta_con_sistema=power_delta_con_sistema + PTred_controler
                    tiempo_anterior=fecha_actual     
                    i=i+1    
                    if i>=n:
                        total_load=total_load+(((power_delta/n)*time_delta)/3600)/1000
                        mes_actual_controler=mes_actual_controler+(((power_delta_con_sistema/n)*time_delta)/3600)/1000
                        sin_sistema_controler=total_load*precio_kwh
                        con_sistema_controler = mes_actual_controler*precio_kwh
                        i=time_delta=power_delta=power_delta_con_sistema=0
                        print("Factura con sistema [COP$]: ",con_sistema_controler)
                        print("Factura sin sistema [COP$]: ", sin_sistema_controler)
                        print("Consumo mes actual [kWh]: ", mes_actual_controler)

                    #print(f'Controlador : En estado {state_provisional} La potencia del Grid es de {PTred_controler} y la potencia de la bateria es de {battery_pow_controler} ...')
                    #print(' ')

                    comunicar_arbol()
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

################################### INICIO ARBOL DE DECISIÓN ###################################
def Arbol_decision():
    global state_controler, P_bateria_decision, PTred_controler,servicio

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
        if VAC_V == True:
            VAC = 1
        else:
            VAC = 0
        return VAC        
    def WAIT():
        global state_controler
        #print(f'Arbol: Probaré el estado {state_controler} ...')
        estado_nuevo.set()
        estado_probado.clear()
        estado_probado.wait()
        #print(f'Arbol: recibí que Servicio es {servicio} y una potencia de la bateria de {P_bateria_decision} ...')
        #print(' ')
    def S_1():
        global servicio, P_bateria_decision, state_controler
        VAC_OS_F = VAC_OSC(servicio)
        if VAC_OS_F == 0:
            state_controler = 3
            WAIT()
            BATT_OS_F = BATT_OSC(P_bateria_decision)
            if BATT_OS_F == 1:
                state_controler = 3
                WAIT()
            else:
                state_controler = 1
                WAIT()
                BATT_OS_F = BATT_OSC(P_bateria_decision)
                if BATT_OS_F == 1:
                    state_controler = 3
                    WAIT()
                else:
                    if HR_OS == 1:
                        state_controler = 2
                        WAIT()
                        BATT_OS_F = BATT_OSC(P_bateria_decision)
                        if BATT_OS_F == 0:
                            state_controler = 2
                        else:
                            state_controler = 1
                            WAIT()
                    else:
                        state_controler = 1
                        WAIT()

        else:
            if HR_OS == 1:
                state_controler = 2
                WAIT()
                BATT_OS_F = BATT_OSC(P_bateria_decision)
                if BATT_OS_F == 1:
                    state_controler = 1
                    WAIT()
                    BATT_OS_F = BATT_OSC(P_bateria_decision)
                    if BATT_OS_F == 1:
                        state_controler = 1
                    else:
                        state_controler = 4
                        WAIT()
                        BATT_OS_F = BATT_OSC(P_bateria_decision)
                        if BATT_OS_F == 1:
                            state_controler = 1
                            WAIT()
                        else:
                            state_controler = 4
                else:
                    state_controler = 2
            else:
                state_controler = 4
                WAIT()
                BATT_OS_F = BATT_OSC(P_bateria_decision)
                if BATT_OS_F == 1:
                    state_controler = 1
                    WAIT()
                else:
                    state_controler = 4
                    
        return state_controler

    estado_probado.wait() 
    BATT_F = P_bateria_decision

    VAC_F = servicio
            
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
    state_controler= 1

    while True:
        while (ahora() < dale + chequeo):
            estado_probado.wait()
            if state_controler== 1:
                state_controler= S_1()
            elif state_controler== 2:
                BATT_OS = BATT_OSC(P_bateria_decision)
                if BATT_OS == 1:
                    state_controler= 1
                else:
                    state_controler= 2
            elif state_controler== 3:
                BATT_OS = BATT_OSC(P_bateria_decision)
                if BATT_OS == 1:
                    state_controler= 3
                else:
                    state_controler= 1
            else:
                BATT_OS = BATT_OSC(P_bateria_decision)
                if BATT_OS == 1:
                    state_controler= 1
                else:
                    state_controler= 4
            estado_nuevo.set()
            estado_probado.set()   
            #print(f'Arbol: El estado del sistema es {state_controler}')
            #print('Arbol: Dormiré 1min...     ')
            #print('    ')
            time.sleep(1*60)
            #print('Arbol: He despertado')
            
        dale = ahora()

################################### INTERFAZ ###################################
def interfaz():
    global text_Turbina,text_Panel,text_Red,text_factor_potencia,text_Bateria,text_Carga,text_horas,text_minutos,text_segundos,text_mes_pasado,text_mes_actual,text_con_sistema
    global text_sin_sistema,text_estado_1,text_estado_2,text_estado_3,text_estado_4,logo_lb_Feliz,logo_lb_Triste,logo_lb_Flecha_Bateria_UP,logo_lb_Flecha_Bateria_D,state_interface
    root = Tk()
    bg_COPor="White"
    font_COPor="#134852"
    root.title("N611 - MONITOR DE CONTROLADOR DE ESTADOS")
    screen_width= root.winfo_screenwidth()  
    screen_height= root.winfo_screenheight() 
    root.geometry("%dx%d" % (screen_width, screen_height)) 
    root.minsize(width=round(0.9*screen_width),height=round(0.9*screen_height))

    #Creating Labels 
    Frame_0=Frame(root, bg="#134852")
    Frame_1=Frame(root,bg=bg_COPor)
    Frame_2=Frame(root,bg=bg_COPor)
    Frame_3=Frame(root,bg=bg_COPor)
    Frame_4=Frame(root,bg=bg_COPor)
    Frame_5=Frame(root,bg=bg_COPor)
    Frame_6=Frame(root,bg=bg_COPor)
    Frame_7=Frame(root,bg=bg_COPor)
    Frame_8=Frame(root,bg=bg_COPor)
    Frame_9=Frame(root,bg=bg_COPor)
    Frame_10=Frame(root,bg=bg_COPor)
    Frame_11=Frame(root,bg=bg_COPor)
    Frame_12=Frame(root,bg=bg_COPor)
    Frame_13=Frame(root,bg=bg_COPor)

    #Creating Logos
    logo_UN=Image.open("imagenes/LogoUninorteB.png")
    resize_logo_UN=logo_UN.resize((195,50))
    logo_UN=ImageTk.PhotoImage(resize_logo_UN)
    logo_lb_UN=Label(Frame_0,image=logo_UN,bg='#32435b')

    logo_Turbina=Image.open("imagenes/Turbina.png")
    resize_logo_Turbina=logo_Turbina.resize((90,110))
    logo_Turbina=ImageTk.PhotoImage(resize_logo_Turbina)
    logo_lb_Turbina=Label(Frame_1,image=logo_Turbina,bg=bg_COPor)

    logo_Panel=Image.open("imagenes/Panel.png")
    resize_logo_Panel=logo_Panel.resize((90,100))
    logo_Panel=ImageTk.PhotoImage(resize_logo_Panel)
    logo_lb_Panel=Label(Frame_2,image=logo_Panel,bg=bg_COPor)

    logo_Red=Image.open("imagenes/Red.png")
    resize_logo_Red=logo_Red.resize((90,100))
    logo_Red=ImageTk.PhotoImage(resize_logo_Red)
    logo_lb_Red=Label(Frame_3,image=logo_Red,bg=bg_COPor)

    logo_Flechas=Image.open("imagenes/FlechasNodo.png")
    resize_logo_Flechas=logo_Flechas.resize((250,450))
    logo_Flechas=ImageTk.PhotoImage(resize_logo_Flechas)
    logo_lb_Flechas=Label(Frame_4,image=logo_Flechas,bg=bg_COPor)

    logo_N611=Image.open("imagenes/casa.png")
    resize_logo_N611=logo_N611.resize((200,200))
    logo_N611=ImageTk.PhotoImage(resize_logo_N611)
    logo_lb_N611=Label(Frame_6,image=logo_N611,bg=bg_COPor) 

    logo_Flecha_Carga=Image.open("imagenes/FlechaCarga.png")
    resize_Flecha_Carga=logo_Flecha_Carga.resize((250,50))
    logo_Flecha_Carga=ImageTk.PhotoImage(resize_Flecha_Carga)
    logo_lb_Flecha_Carga=Label(Frame_8,image=logo_Flecha_Carga,bg=bg_COPor) 

    logo_Carga=Image.open("imagenes/Carga.png")
    resize_Carga=logo_Carga.resize((90,90))
    logo_Carga=ImageTk.PhotoImage(resize_Carga)
    logo_lb_Carga=Label(Frame_9,image=logo_Carga,bg=bg_COPor) 

    logo_Bateria=Image.open("imagenes/Bateria.png")
    resize_Bateria=logo_Bateria.resize((90,90))
    logo_Bateria=ImageTk.PhotoImage(resize_Bateria)
    logo_lb_Bateria=Label(Frame_7,image=logo_Bateria,bg=bg_COPor) 

    logo_Feliz=Image.open("imagenes/feliz.png")
    resize_Feliz=logo_Feliz.resize((70,70))
    logo_Feliz=ImageTk.PhotoImage(resize_Feliz)
    logo_lb_Feliz=Label(Frame_11,image=logo_Feliz,bg=bg_COPor) 

    logo_Triste=Image.open("imagenes/triste.png")
    resize_Triste=logo_Triste.resize((90,90))
    logo_Triste=ImageTk.PhotoImage(resize_Triste)
    logo_lb_Triste=Label(Frame_11,image=logo_Triste,bg=bg_COPor) 

    logo_Flecha_Bateria_UP=Image.open("imagenes/Flecha_bateria.png")
    resize_Flecha_Bateria_UP=logo_Flecha_Bateria_UP.resize((35,130))
    logo_Flecha_Bateria_UP=ImageTk.PhotoImage(resize_Flecha_Bateria_UP)
    logo_lb_Flecha_Bateria_UP=Label(Frame_7,image=logo_Flecha_Bateria_UP,bg=bg_COPor) 

    logo_Flecha_Bateria_D=Image.open("imagenes/Flecha_bateria_D.png")
    resize_Flecha_Bateria_D=logo_Flecha_Bateria_D.resize((35,130))
    logo_Flecha_Bateria_D=ImageTk.PhotoImage(resize_Flecha_Bateria_D)
    logo_lb_Flecha_Bateria_D=Label(Frame_7,image=logo_Flecha_Bateria_D,bg=bg_COPor) 

    #Creating Text
    title=Label(Frame_0,text="N611 - MONITOR DE CONTROLADOR DE ESTADOS",fg="white",bg=font_COPor,font=("Berlin Sans FB Demi",20,"bold"))
    text_Turbina=Label(Frame_1,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    text_Panel=Label(Frame_2,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    text_Red=Label(Frame_3,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    text_factor_potencia=Label(Frame_3,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    state_interface=Label(Frame_5,text="S1",fg=font_COPor,font=('Calibri',40,"bold"),bg=bg_COPor)
    text_Carga=Label(Frame_9,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    text_Bateria=Label(Frame_7,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    Tiempo_servicio=Label(Frame_10,text="Tiempo sin servicio de Red AC: ",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    text_horas=Label(Frame_10,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    text_minutos=Label(Frame_10,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    text_segundos=Label(Frame_10,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    factura=Label(Frame_11,text="Factura:",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    con_sistema=Label(Frame_11,text="Con sistema: COP$",fg=font_COPor,font=("Calibri",15),bg=bg_COPor)
    sin_sistema=Label(Frame_11,text="Sin sistema: COP$",fg=font_COPor,font=("Calibri",15),bg=bg_COPor)
    text_con_sistema=Label(Frame_11,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    text_sin_sistema=Label(Frame_11,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    consumo=Label(Frame_12,text="Consumo:",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    mes_pasado=Label(Frame_12,text="Mes pasado",fg=font_COPor,font=("Calibri",15),bg=bg_COPor)
    mes_actual=Label(Frame_12,text="Mes actual",fg=font_COPor,font=("Calibri",15),bg=bg_COPor)
    text_mes_pasado=Label(Frame_12,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor)
    text_mes_actual=Label(Frame_12,text="0",borderwidth=3, relief="groove",fg=font_COPor,font=("Tahoma",12),bg=bg_COPor) 
    Firma=Label(Frame_13,text="Φ Natalia González Mackenzie - Proyecto Final Ing. Electrónica 2022-10",fg=font_COPor,font=("Calibri",12,"italic"),bg=bg_COPor)
    unidad_turbina=Label(Frame_1,text="W",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    unidad_panel=Label(Frame_2,text="W",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    unidad_red=Label(Frame_3,text="W",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    unidad_bateria=Label(Frame_7,text="W",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    unidad_carga=Label(Frame_9,text="W",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    unidad_mes_pasado=Label(Frame_12,text="kW/h",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    unidad_mes_actual=Label(Frame_12,text="kW/h",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    
    unidad_horas=Label(Frame_10,text="horas",fg=font_COPor,font=("Calibri",15),bg=bg_COPor)
    unidad_minutos=Label(Frame_10,text="minutos",fg=font_COPor,font=("Calibri",15),bg=bg_COPor)
    unidad_segundos=Label(Frame_10,text="segundos",fg=font_COPor,font=("Calibri",15),bg=bg_COPor)
    text_estado_1=Label(Frame_5,text="NORMAL",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    text_estado_2=Label(Frame_5,text="AHORRO",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    text_estado_3=Label(Frame_5,text="RESPALDO",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    text_estado_4=Label(Frame_5,text="EFICIENCIA",fg=font_COPor,font=("Calibri",15,"bold"),bg=bg_COPor)
    
    #Placing Frames
    Frame_0.place(relx=0,rely=0,relwidth=1,relheight=0.1)
    Frame_1.place(relx=0,rely=0.1,relwidth=0.17,relheight=0.25)
    Frame_2.place(relx=0,rely=0.35,relwidth=0.17,relheight=0.25)
    Frame_3.place(relx=0,rely=0.6,relwidth=0.17,relheight=0.25)
    Frame_4.place(relx=0.17,rely=0.1,relwidth=0.24,relheight=0.75)
    Frame_5.place(relx=0.41,rely=0.1,relwidth=0.17,relheight=0.25)
    Frame_6.place(relx=0.41,rely=0.35,relwidth=0.17,relheight=0.166)
    Frame_7.place(relx=0.41,rely=0.516,relwidth=0.17,relheight=0.334)
    Frame_10.place(relx=0.58,rely=0.1,relwidth=0.42,relheight=0.25)
    Frame_8.place(relx=0.58,rely=0.35,relwidth=0.25,relheight=0.5)
    Frame_9.place(relx=0.83,rely=0.35,relwidth=0.17,relheight=0.5)
    Frame_11.place(relx=0,rely=0.85,relwidth=0.5,relheight=0.11)
    Frame_12.place(relx=0.5,rely=0.85,relwidth=0.5,relheight=0.11)
    Frame_13.place(relx=0,rely=0.96,relwidth=1,relheight=0.04)

    #Placing Logos
    logo_lb_UN.place(relx=0.75,rely=0.25,relwidth=0.3,relheight=0.5)
    logo_lb_Turbina.place(relx=0.31,rely=0.15,relwidth=0.4,relheight=0.7)
    logo_lb_Panel.place(relx=0.32,rely=0.15,relwidth=0.41,relheight=0.5)
    logo_lb_Red.place(relx=0.33,rely=0.05,relwidth=0.35,relheight=0.4)
    logo_lb_Flechas.place(relx=0,rely=0,relwidth=1,relheight=1)
    logo_lb_N611.place(relx=0,rely=0,relwidth=1,relheight=1)
    logo_lb_Flecha_Carga.place(relx=0,rely=0.2,relwidth=1,relheight=0.1)
    logo_lb_Carga.place(relx=0.1,rely=0.1,relwidth=0.45,relheight=0.2)
    logo_lb_Bateria.place(relx=0.25,rely=0.5,relwidth=0.5,relheight=0.3)
    logo_lb_Feliz.place(relx=0.7,rely=0,relwidth=0.3,relheight=1)
    logo_lb_Flecha_Bateria_UP.place(relx=0.4,rely=0,relwidth=0.15,relheight=0.5)

    #Placing Labels
    title.place(relx=0.02,rely=0.25,relwidth=0.6,relheight=0.5)
    text_Turbina.place(relx=0.3,rely=0.75,relwidth=0.45,relheight=0.2)
    text_Panel.place(relx=0.3,rely=0.55,relwidth=0.45,relheight=0.2)
    text_Red.place(relx=0.3,rely=0.5,relwidth=0.45,relheight=0.2)
    text_factor_potencia.place(relx=0.3,rely=0.75,relwidth=0.45,relheight=0.2)
    text_Bateria.place(relx=0.27,rely=0.8,relwidth=0.45,relheight=0.15)
    text_Carga.place(relx=0.1,rely=0.32,relwidth=0.45,relheight=0.1)
    text_horas.place(relx=0.05,rely=0.7,relwidth=0.1,relheight=0.15)
    text_minutos.place(relx=0.3,rely=0.7,relwidth=0.1,relheight=0.15)
    text_segundos.place(relx=0.6,rely=0.7,relwidth=0.1,relheight=0.15)
    text_mes_pasado.place(relx=0.55,rely=0.2,relwidth=0.2,relheight=0.3)
    text_mes_actual.place(relx=0.55,rely=0.55,relwidth=0.2,relheight=0.3)
    text_con_sistema.place(relx=0.55,rely=0.2,relwidth=0.2,relheight=0.3)
    text_sin_sistema.place(relx=0.55,rely=0.55,relwidth=0.2,relheight=0.3)

    state_interface.place(relx=0.3333,rely=0.2,relwidth=0.3334,relheight=0.3)
    text_estado_1.place(relx=0.25,rely=0.5,relwidth=0.5,relheight=0.15)
    Tiempo_servicio.place(relx=0.1,rely=0.5,relwidth=0.67,relheight=0.2)
    consumo.place(relx=0.15,rely=0.25,relwidth=0.2,relheight=0.2)
    con_sistema.place(relx=0.23,rely=0.25,relwidth=0.3,relheight=0.2)
    sin_sistema.place(relx=0.23,rely=0.6,relwidth=0.3,relheight=0.2)
    factura.place(relx=0.05,rely=0.25,relwidth=0.17,relheight=0.2)
    mes_pasado.place(relx=0.35,rely=0.25,relwidth=0.2,relheight=0.2)
    mes_actual.place(relx=0.35,rely=0.6,relwidth=0.2,relheight=0.2)

    unidad_turbina.place(relx=0.75,rely=0.75,relwidth=0.2,relheight=0.2)
    unidad_panel.place(relx=0.75,rely=0.55,relwidth=0.2,relheight=0.2)
    unidad_red.place(relx=0.75,rely=0.5,relwidth=0.2,relheight=0.2)
    unidad_bateria.place(relx=0.75,rely=0.8,relwidth=0.2,relheight=0.2)
    unidad_carga.place(relx=0.55,rely=0.32,relwidth=0.2,relheight=0.1)
    unidad_horas.place(relx=0.16,rely=0.7,relwidth=0.1,relheight=0.15)
    unidad_minutos.place(relx=0.41,rely=0.7,relwidth=0.15,relheight=0.15)
    unidad_segundos.place(relx=0.7,rely=0.7,relwidth=0.2,relheight=0.15)
    unidad_mes_pasado.place(relx=0.75,rely=0.2,relwidth=0.15,relheight=0.3)
    unidad_mes_actual.place(relx=0.75,rely=0.55,relwidth=0.15,relheight=0.3)
    Firma.place(relx=0,rely=0.4,relwidth=0.5,relheight=0.4)

    root.mainloop()

def Actualizar_Interfaz():
    global text_Turbina,text_Panel,text_Red,text_factor_potencia,text_Bateria,text_Carga,text_horas,text_minutos,text_segundos,text_mes_pasado,text_mes_actual,text_con_sistema
    global text_sin_sistema,text_estado_1,text_estado_2,text_estado_3,text_estado_4,logo_lb_Triste,logo_lb_Feliz,logo_lb_Flecha_Bateria_UP,logo_lb_Flecha_Bateria_D,state_interface
    global wt_power_controler,panel_power_controler,PTred_controler,FPred_controler,load_pow_controler,battery_pow_controler,mes_actual_controler,mes_anterior_controler,con_sistema_controler,sin_sistema_controler,tiempo_sin_servicio_controler,state_provisional
    
    while True:
        #Cambio de texto
        nuevas_variables_controlador.wait()
        nuevas_variables_controlador.clear()
        
        state_interface.config(text="S"+ str(state_provisional))
        text_Turbina.config(text=round(wt_power_controler,3))
        text_Panel.config(text=round(panel_power_controler,3))
        text_Red.config(text=round(PTred_controler,3))
        text_factor_potencia.config(text=round(FPred_controler,3))
        text_Carga.config(text=round(load_pow_controler,3))
        text_Bateria.config(text=round(battery_pow_controler,3))
        text_mes_actual.config(text=round(mes_actual_controler,3))
        text_mes_pasado.config(text=round(mes_anterior_controler,3))
        text_con_sistema.config(text=round(con_sistema_controler,3))
        text_sin_sistema.config(text=round(sin_sistema_controler,3))

        text_horas.config(text=round(tiempo_sin_servicio_controler.total_seconds())//3600)
        text_minutos.config(text=round((tiempo_sin_servicio_controler.total_seconds()%3600)//60))
        text_segundos.config(text=round((tiempo_sin_servicio_controler.total_seconds()%60)))

        #Cmbio de logos
        if state_provisional==1:
            text_estado_1.place(relx=0.25,rely=0.5,relwidth=0.5,relheight=0.15)
        elif state_provisional==2:
            text_estado_2.place(relx=0.25,rely=0.5,relwidth=0.5,relheight=0.15)
        elif state_provisional==3:
            text_estado_3.place(relx=0.25,rely=0.5,relwidth=0.5,relheight=0.15)
        else:
            text_estado_4.place(relx=0.25,rely=0.5,relwidth=0.5,relheight=0.15)

        if con_sistema_controler>sin_sistema_controler:
            logo_lb_Feliz.place_forget()
            logo_lb_Triste.place(relx=0.7,rely=0,relwidth=0.3,relheight=1)
        else:
            logo_lb_Triste.place_forget()
            logo_lb_Feliz.place(relx=0.7,rely=0,relwidth=0.3,relheight=1)

        if battery_pow_controler<0:
            logo_lb_Flecha_Bateria_UP.place_forget()
            logo_lb_Flecha_Bateria_D.place(relx=0.4,rely=0,relwidth=0.15,relheight=0.5)
        else:
            logo_lb_Flecha_Bateria_D.place_forget()
            logo_lb_Flecha_Bateria_UP.place(relx=0.4,rely=0,relwidth=0.15,relheight=0.5)

def consumo_recursos():
    uso_cpu=[]
    uso_ram=[]
    while True:
        uso_cpu.append(psutil.cpu_percent(1))
        print('The CPU usage is: ', uso_cpu)
        uso_ram.append(psutil.virtual_memory()[2])
        print('RAM memory used:', uso_ram) 
        time.sleep(5)


estado_nuevo = threading.Event() #Le dice al controlador qué debe hacer
estado_probado = threading.Event() #Le dice al arbol qué debe hacer
nuevas_variables_controlador = threading.Event()

thread_control = threading.Thread(target=Controlador)
thread_arbol = threading.Thread(target=Arbol_decision)
thread_interfaz = threading.Thread(target=interfaz)
thread_Actualizar_Interfaz=threading.Thread(target=Actualizar_Interfaz)
thread_consumo_recursos = threading.Thread(target=consumo_recursos)

thread_interfaz.start()
thread_control.start()
thread_Actualizar_Interfaz.start()
thread_arbol.start()
