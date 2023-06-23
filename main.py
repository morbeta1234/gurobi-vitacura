from gurobipy import GRB, Model, quicksum # type: ignore
# from random import randint, random, seed
import pandas as pd

model = Model()

model.setParam('TimeLimit', 30 * 60)


# LECTURA BASE DE DATOS Y PARAMETROS
bd_params = pd.read_excel("Parametros_unicos.xlsx")
bd_areasparques = pd.read_excel("solo_m2_areas.xlsx")
bd_obras = pd.read_excel("Costo_Obras.xlsx")
bd_vegetacion_hoja1 = pd.read_excel("plantas.xlsx", sheet_name = 'Arboles')
bd_vegetacion_hoja2 = pd.read_excel("plantas.xlsx", sheet_name = 'Pasto')
bd_vegetacion_hoja3 = pd.read_excel("plantas.xlsx", sheet_name = 'Arbustos')

# SETS
H = range(24) # Horas
D = range(365) # Dias
A = range(bd_areasparques.shape[0]) # Areas
J = range(bd_vegetacion_hoja1.shape[0]) # Arboles
N = range(bd_vegetacion_hoja3.shape[0]) # Arbustos

# BigM
M = 10000000000000000000000


# PARAMS
P = bd_params.iloc[0,1] # FILA 0 COLUMNA 1  P = 97388 # Poblacion Vitacura
# print(f"P: {P}")
AR = bd_params.iloc[1,1] # FILA 0 COLUMNA 1  AR = 9 # M2 de area verde recomendada por OMS
# print(f"AR:{AR}") 
COI = bd_params.iloc[2,1] # FILA 0 COLUMNA 1  COI = 39780 # Costo por m2 por instalar obra
# print(f"COI:{COI}")
PT = bd_params.iloc[3,1] # FILA 0 COLUMNA 1  PT = 723248 # Presupuesto total comuna de Vitacura
# PT= 0
# print(f"PT:{PT}")
AT = bd_areasparques['Área'].tolist() # Area total de cada area a
# print(f"AT:{AT}")
APJ = bd_vegetacion_hoja1['Area Promedio (en m2)'].tolist() # Area promedio j-esimo arbol
# print(f"APJ:{APJ}")
CPA = bd_vegetacion_hoja1['Precio Plantación'].tolist() # Costo de plantar arbol j
# print(f"CPA:{CPA}")
CRA = bd_vegetacion_hoja1['Precio transplante (sacado)'].tolist()  # Costo de remover arbol j
# print(f"CRA:{CRA}")
CPI = bd_vegetacion_hoja1['consuma de agua en invierno (en m3)'].tolist() # Consumo de agua de arbol j en invierno
# print(f"CPI:{CPI}")
CPV = bd_vegetacion_hoja1['consumo de agua en verano'].tolist()  # Consumo de agua arbol j en verano
# print(f"CPV:{CPV}")
CAPV = bd_vegetacion_hoja2['agua necesaria por metro cuadrado (Verano)'].tolist()[0] # Consumo de agua por m2 de pasto en verano
# print(f"CAPV:{CAPV}")
CAPI = bd_vegetacion_hoja2['agua necesaria por metro cuadrado (Invierno)'].tolist()[0] # Consumo de agua por m2 de pasto en invierno
# print(f"CAPI:{CAPI}")
CPP = bd_vegetacion_hoja2['instalacion de pasto'].tolist()[0] # Costo de plantar m2 pasto
# print(f"CPP:{CPP}")
CPR = bd_vegetacion_hoja2['remocion de pasto'].tolist()[0] # Costo de remover m2 pasto
# print(f"CRP:{CPR}")
APN = bd_vegetacion_hoja3['area ocupada por la planta (m2)'].tolist() # Area promedio n-esimo arbusto
# print(f"APN:{APN}")
CAV = bd_vegetacion_hoja3['m3 por arbusto [diario] (VERANO)'].tolist() # Consumo de agua de arbusto n en verano
# print(f"CAV:{CAV}")
CAI = bd_vegetacion_hoja3['m3  por arbusto [diario] (INVIERNO)'].tolist() # Consumo de agua de arbusto n en invierno
# print(f"CAI:{CAI}")
CPAN = bd_vegetacion_hoja3['precio instalar 1 planta'].tolist() # Costo de plantar arbusto n
# print(f"CPAN:{CPAN}")
CRAN = bd_vegetacion_hoja3['precio sacar'].tolist() # Costo de remover arbusto n
# print(f"CRAN:{CRAN}")
PMV = 0.5 # Porcentaje minimo de area verde en cada area
RAAJ = 0.2 # Porcentaje maximo de area de arboles en cada area
RAAN = 0.1 # Porcentaje maximo de area de arbustos en cada area
RAP = 0.3 # Porcentaje minimo de area de pasto en cada area



# VARIABLES
# E = model.addVars(D, vtype = GRB.BINARY, name = "E") # E_d: Epoca del año (1 verano, 0 invierno)
AO = model.addVars(A, vtype = GRB.CONTINUOUS, name = "AO") # AO_a: Area de obras en a 
V = model.addVars(J, A, vtype = GRB.BINARY, name = "V") # V_j,a: Presente especie j de arbol en a 
U = model.addVars(N, A, vtype = GRB.BINARY, name = "U") # U_n,a: Presente especie n de arbusto en a 
CAJ = model.addVars(J, A, vtype = GRB.INTEGER, name = "CAJ") # CAJ_j,a: Cantidad de arboles j en a 
CAN = model.addVars(N, A, vtype = GRB.INTEGER, name = "CAN") # CAN_n,a: Cantidad de arbustos n en a 
AP = model.addVars(A, vtype = GRB.CONTINUOUS, name = "AP") # AP_a: Area de pasto en a 
PA = model.addVars(J, A, vtype = GRB.INTEGER, name = "PA") # PA_j,a: Cantidad de arboles j plantados en a 
RA = model.addVars(J, A, vtype = GRB.INTEGER, name = "RA") # RA_j,a: Cantidad de arboles j removidos en a
PAN = model.addVars(N, A, vtype = GRB.INTEGER, name = "PAN") # PAN_n,a: Cantidad de arbustos n plantados en a 
RAN = model.addVars(N, A, vtype = GRB.INTEGER, name = "RAN") # RAN_n,a: Cantidad de arbustos n removidos en a 
AIA = model.addVars(A, vtype = GRB.CONTINUOUS, name = "AIA") # AIA_a: Area instalada de pasto en a 
ARA = model.addVars(A, vtype = GRB.CONTINUOUS, name = "ARA") # ARA_a: Area removida de pasto en a 
AIO = model.addVars(A, vtype = GRB.CONTINUOUS, name = "AIO") # AIO_a: Area instalada de obras en a 
R = model.addVars(A, vtype = GRB.CONTINUOUS, name = "R")

model.update()


# CONSTRAINTS
# C1: Existe una division entre verano e invierno
# model.addConstr(quicksum(E[d] for d in D) == 183, name="C1")

# C2: La mitad del tiempo es verano, el resto invierno
# model.addConstrs((E[d] == 1 for d in D if d <= 183), name="C2")

# C3: Area utilizada por pasto, arboles, arbustos y obras debe ser igual al area total
model.addConstrs((AT[a] == AO[a] + AP[a] + quicksum(CAJ[j,a] * APJ[j] for j in J) + quicksum(CAN[n,a] for n in N) for a in A), name="C3")

# C4 Area verde por habitante debe ser mayor o igual a lo recomendado por la OMS
model.addConstr((quicksum((AT[a] - AO[a]) for a in A) >= AR * P), name="C4") # type: ignore

# C5: No se puede regar entre las 9 y las 20 horas
# model.addConstrs((R[a,h,d] == 0 for a in A for h in H if h >= 9 and h <= 20 for d in D), name="C5")

# C6: Agua utilizada para regar un area debe ser igual al consumo de la vegetacion presente en el area
model.addConstrs(((R[a]== quicksum((CPV[j] * 183 + CPI[j] * 183) * CAJ[j,a] for j in J)  + quicksum((CAV[n] * 183 + CAI[n] *183) * CAN[n,a] for n in N)+ AP[a] * (CAPV *183 + CAPI * 183) )for a in A) , name="C6")

# C7: Area de vegetacion en cada area debe ser mayor o igual al minimo establecido
model.addConstrs(((quicksum(CAJ[j,a] * APJ[j] for j in J) + quicksum(CAN[n,a] * APN[n] for n in N) + AP[a] >= AT[a] * PMV) for a in A), name="C7")

# C8: La suma de todos los arboles debe ser al menos 1/3 de la poblacion, segun recomendacion de OMS
model.addConstr((quicksum(quicksum((CAJ[j,a] for j in J)) for a in A) >= P / 3), name="C8") # type: ignore

# C9: Debe haber al menos 3 especies de arboles en cada area
model.addConstrs((quicksum((V[j,a] for j in J)) >= 3 for a in A ), name="C9")

# C10: Debe haber al menos 3 especies de arbustos en cada area
model.addConstrs((quicksum((U[n,a] for n in N)) >= 3 for a in A), name="C10")

# C11: Solo puede haber arboles plantados de una especie si esta esta presente en el area
model.addConstrs((CAJ[j,a] <= M * V[j,a] for j in J for a in A), name="C11")

# C12: Solo puede haber arbustos plantados de una especie si esta esta presente en el area
model.addConstrs((CAN[n,a] <= M * U[n,a] for n in N for a in A ), name="C12")

# C13: La cantidad de arboles debe ser igual que lo presente el dia anterior, menos lo removido y mas lo plantado.
# model.addConstrs(quicksum(CAJ[j,a,d] for j in J) == quicksum(CAJ[j,a,d-1] + PA[j,a,d] - RA[j,a,d] for j in J) for a in A for d in D if d > 1)

# C14: La cantidad de arbustos debe ser igual que lo presente el dia anterior, menos lo removido y mas lo plantado.
# model.addConstrs(quicksum(CAN[n,a,d] for n in N) == quicksum(CAN[n,a,d-1] + PAN[n,a,d] - RAN[n,a,d] for n in N) for a in A for d in D if d > 1)

# C15: La cantidad de pasto instalado debe ser igual que lo presente el dia anterior, menos lo removido y mas lo plantado.
# model.addConstrs(AP[a,d] == AP[a, d-1] + AIA[a,d] - ARA[a, d] for a in A for d in D if d > 1)

# C16: La cantidad de obras instaladas debe ser igual que lo presente el dia anterior, menos lo removido y mas lo plantado.
# model.addConstrs(AO[a,d] == AO[a, d-1] + AIO[a,d] - ARO[a, d] for a in A for d in D if d > 1)

# C17: Los costos de obras y movimientos de vegetacion no deben superar el presupuesto total.
model.addConstr((quicksum(COI * AO[a] + 
                            CPP * AIA[a]+
                            CPR * ARA[a]+
                            quicksum(CPAN[n] * PAN[n,a,]+ CRAN[n] * RAN[n,a] for n in N) +
                            quicksum(CPA[j] * PA[j,a]+ CRA[j] *RA[j,a] for j in J) 
                            for a in A) <= PT), name="C17")


# model.addConstrs((CAJ[j,a] <= V[j,a]*quicksum(CAJ[j,a] for j in J) for j in J for a in A), name="C18")

# model.addConstrs((CAN[n,a] <= U[n,a]*quicksum(CAN[n,a] for n in N) for n in N for a in A), name="C19")

model.addConstrs((CAJ[j,a] >= V[j,a] for j in J for a in A), name="C18")

model.addConstrs((CAN[n,a] >= U[n,a] for n in N for a in A), name="C19")

model.addConstrs((quicksum(CAJ[j,a] * APJ[j] for j in J) <= AT[a] * RAAJ for a in A), name="C20" )

model.addConstrs((quicksum(CAN[n,a] * APN[n] for n in N) <= AT[a] * RAAN for a in A), name="C21" )

model.addConstrs((AO[a] * COI >= 0 for a in A), name="C22" )

model.addConstrs((AP[a]  >= AT[a] * RAP for a in A), name="C23" )


model.update()

# OBJECTIVE FUNCTION
FO = quicksum(R[a]  for a in A)
model.setObjective(FO, GRB.MINIMIZE)

model.optimize()

# model.printAttr('X')
model.write("modelo.json")
for a in A:
    print(f"AO_{a}: {AO[a].x}") if AO[a].x < 0 else None
    print(f"AT_{a}: {AT[a]}") if AT[a] < 0 else None
    print(f"AF_{a}: {AT[a]-AO[a].x}") if AT[a]-AO[a].x < 0 else None
    for j in J:
        print(f"V_{j}_{a}: {V[j,a] .x}") if V[j,a] .x < 0 else None
        print(f"CAJ{j}_{a}: {CAJ[j,a] .x}") if CAJ[j,a] .x < 0 else None

    