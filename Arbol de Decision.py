import numpy as np
import time
import datetime


def ahora():
    ahora_time = datetime.datetime.now()
    ahora_hora = ahora_time.hour
    ahora_minuto = ahora_time.minute
    ahora_segundo = ahora_time.second
    ahora_ya = ahora_hora + (ahora_minuto/60) + (ahora_segundo/3600)
    return ahora_ya

def HR_OSC():                               #Obtener el Flag "HR" del OSC
    # Hora de Interés 10:45 AM a 2:45 PM
    inicio_ventana_interes = 10 + 45/60     # Check WeatherUnderground
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
    print('Tensión de AC?  ')
    VAC_F_F = float(input())
    VAC_OS_F = VAC_OSC(VAC_F_F)
    if VAC_OS_F == 0:
        S_OSC_F = 3
        time.sleep(2)
        print('Potencia de la Batería?    ')
        BATT_F_F = float(input())
        BATT_OS_F = BATT_OSC(BATT_F_F)
        if BATT_OS_F == 1:
            S_OSC_F = 3
            time.sleep(2)
        else:
            S_OSC_F = 1
            time.sleep(2)
            print('Potencia de la Batería?    ')
            BATT_F_F = float(input())
            BATT_OS_F = BATT_OSC(BATT_F_F)
            if BATT_OS_F == 1:
                S_OSC_F = 3
                time.sleep(2)
            else:
                if HR_OS == 1:
                    S_OSC_F = 2
                    time.sleep(2)
                    print('Potencia de la Batería?    ')
                    BATT_F_F = float(input())
                    BATT_OS_F = BATT_OSC(BATT_F_F)
                    if BATT_OS_F == 0:
                        S_OSC_F = 2
                    else:
                        S_OSC_F = 1
                        time.sleep(2)
                else:
                    S_OSC_F = 1
                    time.sleep(2)

    else:
        if HR_OS == 1:
            S_OSC_F = 2
            time.sleep(2)
            print('Potencia de la Batería?    ')
            BATT_F_F = float(input())
            BATT_OS_F = BATT_OSC(BATT_F_F)
            if BATT_OS_F == 1:
                S_OSC_F = 1
                time.sleep(2)
                print('Potencia de la Batería?    ')
                BATT_F_F = float(input())
                BATT_OS_F = BATT_OSC(BATT_F_F)
                if BATT_OS_F == 1:
                    S_OSC_F = 1
                else:
                    S_OSC_F = 4
                    time.sleep(2)
                    print('Potencia de la Batería?    ')
                    BATT_F_F = float(input())
                    BATT_OS_F = BATT_OSC(BATT_F_F)
                    if BATT_OS_F == 1:
                        S_OSC_F = 1
                        time.sleep(2)
                    else:
                        S_OSC_F = 4
            else:
                S_OSC_F = 2
        else:
            S_OSC_F = 4
            time.sleep(2)
            print('Potencia de la Batería?    ')
            BATT_F_F = float(input())
            BATT_OS_F = BATT_OSC(BATT_F_F)
            if BATT_OS_F == 1:
                S_OSC_F = 1
                time.sleep(2)
            else:
                S_OSC_F = 4
                  
    return S_OSC_F

     
print('Ingrese la potencia de la Batería   ')
BATT_F = float(input())

print('Ingrese la tensión del Grid   ')
VAC_F = float(input())
        
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
S_OSC = 1

while True:
    while (ahora() < dale + chequeo):
        if S_OSC == 1:
            S_OSC = S_1()
        elif S_OSC == 2:
            print('Potencia de la Batería?    ')
            BATT_F = float(input())
            BATT_OS = BATT_OSC(BATT_F)
            if BATT_OS == 1:
                S_OSC = 1
            else:
                S_OSC = 2
        elif S_OSC == 3:
            print('Potencia de la Batería?    ')
            BATT_F = float(input())
            BATT_OS = BATT_OSC(BATT_F)
            if BATT_OS == 1:
                S_OSC = 3
            else:
                S_OSC = 1
        else:
            print('Potencia de la Batería?    ')
            BATT_F = float(input())
            BATT_OS = BATT_OSC(BATT_F)
            if BATT_OS == 1:
                S_OSC = 1
            else:
                S_OSC = 4

        print('    ')
        print('El estado del sistema es...     ')
        print(S_OSC)
        print('    ')
        print('Waiting...     ')
        print('    ')
        time.sleep(2*60)
        
    dale = ahora()
    
    
