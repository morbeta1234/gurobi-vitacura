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
AR = bd_params.iloc[1,1] # FILA 0 COLUMNA 1  AR = 9 # M2 de area verde recomendada por OMS 
COI = bd_params.iloc[2,1] # FILA 0 COLUMNA 1  COI = 39780 # Costo por m2 por instalar obra
COR = bd_obras.iloc[19,7] # Area total de cada area 39780.97 # Costo por m2 por remover obra
PT = bd_params.iloc[3,1] # FILA 0 COLUMNA 1  PT = 723248 # Presupuesto total comuna de Vitacura
AT = bd_areasparques['Área'].tolist() # Area total de cada area a
APJ = bd_vegetacion_hoja1['Area Promedio (en m2)'].tolist() # Area promedio j-esimo arbol
CPA = bd_vegetacion_hoja1['Precio Plantación'].tolist() # Costo de plantar arbol j
CRA = bd_vegetacion_hoja1['Precio transplante (sacado)'].tolist()  # Costo de remover arbol j
CPI = bd_vegetacion_hoja1['consuma de agua en invierno (en m3)'].tolist() # Consumo de agua de arbol j en invierno
CPV = bd_vegetacion_hoja1['consumo de agua en verano'].tolist()  # Consumo de agua arbol j en verano
CAPV = bd_vegetacion_hoja2['agua necesaria por metro cuadrado (Verano)'].tolist()[0] # Consumo de agua por m2 de pasto en verano
CAPI = bd_vegetacion_hoja2['agua necesaria por metro cuadrado (Invierno)'].tolist()[0] # Consumo de agua por m2 de pasto en invierno
CPP = bd_vegetacion_hoja2['instalacion de pasto'].tolist()[0] # Costo de plantar m2 pasto
CPR = bd_vegetacion_hoja2['remocion de pasto'].tolist()[0] # Costo de remover m2 pasto
APN = bd_vegetacion_hoja3['area ocupada por la planta (m2)'].tolist() # Area promedio n-esimo arbusto
CAV = bd_vegetacion_hoja3[' m3 por semana por metro cuadrado de planta (VERANO)'].tolist() # Consumo de agua de arbusto n en verano
CAI = bd_vegetacion_hoja3['m3 por semana por metro cuadrado (INVIERNO)'].tolist() # Consumo de agua de arbusto n en invierno
CPAN = bd_vegetacion_hoja3['precio instalar 1 planta'].tolist() # Costo de plantar arbusto n
CRAN = bd_vegetacion_hoja3['precio sacar'].tolist() # Costo de remover arbusto n
PA = 0.5 # Porcentaje minimo de area verde en cada area


# VARIABLES
E = model.addVars(D, vtype = GRB.BINARY, name = "E") # E_d: Epoca del año (1 verano, 0 invierno)
R = model.addVars(A, H, D, vtype = GRB.CONTINUOUS, name = "R") # R_a,h,d : Cantidad de agua necesaria para regar vegentacion en a a la hora h del dia d
AO = model.addVars(A, D, vtype = GRB.CONTINUOUS, name = "AO") # AO_a,d: Area de obras en a en el dia d
V = model.addVars(J, A, D, vtype = GRB.BINARY, name = "V") # V_j,a,d: Presente especie j de arbol en a en el dia d
U = model.addVars(N, A, D, vtype = GRB.BINARY, name = "U") # U_n,a,d: Presente especie n de arbusto en a en el dia d
CAJ = model.addVars(J, A, D, vtype = GRB.INTEGER, name = "CAJ") # CAJ_j,a,d: Cantidad de arboles j en a en el dia d
CAN = model.addVars(N, A, D, vtype = GRB.INTEGER, name = "CAN") # CAN_n,a,d: Cantidad de arbustos n en a en el dia d
AP = model.addVars(A, D, vtype = GRB.CONTINUOUS, name = "AP") # AP_a,d: Area de pasto en a en el dia d
PA = model.addVars(J, A, D, vtype = GRB.INTEGER, name = "PA") # PA_j,a,d: Cantidad de arboles j plantados en a en el dia d
RA = model.addVars(J, A, D, vtype = GRB.INTEGER, name = "RA") # RA_j,a,d: Cantidad de arboles j removidos en a en el dia d
PAN = model.addVars(N, A, D, vtype = GRB.INTEGER, name = "PAN") # PAN_n,a,d: Cantidad de arbustos n plantados en a en el dia d
RAN = model.addVars(N, A, D, vtype = GRB.INTEGER, name = "RAN") # RAN_n,a,d: Cantidad de arbustos n removidos en a en el dia d
AIA = model.addVars(A, D, vtype = GRB.CONTINUOUS, name = "AIA") # AIA_a,d: Area instalada de pasto en a en el dia d
ARA = model.addVars(A, D, vtype = GRB.CONTINUOUS, name = "ARA") # ARA_a,d: Area removida de pasto en a en el dia d
AIO = model.addVars(A, D, vtype = GRB.CONTINUOUS, name = "AIO") # AIO_a,d: Area instalada de obras en a en el dia d
ARO = model.addVars(A, D, vtype = GRB.CONTINUOUS, name = "ARO") # ARO_a,d: Area removida de obras en a en el dia d

model.update()


# CONSTRAINTS
# C1: Existe una division entre verano e invierno
model.addConstr(quicksum(E[d] for d in D) == 183, name="C1")

# C2: La mitad del tiempo es verano, el resto invierno
model.addConstrs((E[d] == 1 for d in D if d <= 183), name="C2")

# C3: Area utilizada por pasto, arboles, arbustos y obras debe ser igual al area total
model.addConstrs((AT[a] == AO[a, d] + AP[a,d] + quicksum(CAJ[j,a,d] * APJ[j] for j in J) + quicksum(CAN[n,a,d] for n in N) for a in A for d in D), name="C3")

# C4 Area verde por habitante debe ser mayor o igual a lo recomendado por la OMS
model.addConstrs((quicksum((AT[a] - AO[a,d]) for a in A) >= AR * P for d in D), name="C4") # type: ignore

# C5: No se puede regar entre las 9 y las 20 horas
model.addConstrs((R[a,h,d] == 0 for a in A for h in H if h >= 9 and h <= 20 for d in D), name="C5")

# C6: Agua utilizada para regar un area debe ser igual al consumo de la vegetacion presente en el area
model.addConstrs((quicksum(R[a,h,d] for h in H) <= quicksum((CPV[j] * E[d] + CPI[j] * (1 - E[d])) * CAJ[j,a,d] for j in J) + quicksum((CAV[n] * E[d] + CAI[n] * (1 - E[d])) * CAN[n,a,d] for n in N) + AP[a,d] * (CAPV * E[d] + CAPI * (1 - E[d])) for d in D for a in A) , name="C6")

# C7: Area de vegetacion en cada area debe ser mayor o igual al minimo establecido
#model.addConstrs(((quicksum(CAJ[j,a,d] * APJ[j] for j in J) + quicksum(CAN[n,a,d] * APN[n] for n in N) + AP[a,d] >= AT[a] * PA) for a in A for d in D), name="C7")

# C8: La suma de todos los arboles debe ser al menos 1/3 de la poblacion, segun recomendacion de OMS
model.addConstrs((quicksum(quicksum((CAJ[j,a,d] for j in J)) for a in A) >= P / 3 for d in D), name="C8") # type: ignore

# C9: Debe haber al menos 3 especies de arboles en cada area
model.addConstrs((quicksum((V[j,a,d] for j in J)) >= 3 for a in A for d in D), name="C9")

# C10: Debe haber al menos 3 especies de arbustos en cada area
model.addConstrs((quicksum((U[n,a,d] for n in N)) >= 3 for a in A for d in D), name="C10")

# C11: Solo puede haber arboles plantados de una especie si esta esta presente en el area
model.addConstrs((CAJ[j,a,d] <= M * V[j,a,d] for j in J for a in A for d in D), name="C11")

# C12: Solo puede haber arbustos plantados de una especie si esta esta presente en el area
model.addConstrs((CAN[n,a,d] <= M * U[n,a,d] for n in N for a in A for d in D), name="C12")

# C13: La cantidad de arboles debe ser igual que lo presente el dia anterior, menos lo removido y mas lo plantado.
model.addConstrs(quicksum(CAJ[j,a,d] for j in J) == quicksum(CAJ[j,a,d-1] + PA[j,a,d] - RA[j,a,d] for j in J) for a in A for d in D if d > 1)

# C14: La cantidad de arbustos debe ser igual que lo presente el dia anterior, menos lo removido y mas lo plantado.
model.addConstrs(quicksum(CAN[n,a,d] for n in N) == quicksum(CAN[n,a,d-1] + PAN[n,a,d] - RAN[n,a,d] for n in N) for a in A for d in D if d > 1)

# C15: La cantidad de pasto instalado debe ser igual que lo presente el dia anterior, menos lo removido y mas lo plantado.
model.addConstrs(AP[a,d] == AP[a, d-1] + AIA[a,d] - ARA[a, d] for a in A for d in D if d > 1)

# C16: La cantidad de obras instaladas debe ser igual que lo presente el dia anterior, menos lo removido y mas lo plantado.
model.addConstrs(AO[a,d] == AO[a, d-1] + AIO[a,d] - ARO[a, d] for a in A for d in D if d > 1)

# C17: Los costos de obras y movimientos de vegetacion no deben superar el presupuesto total.
model.addConstr((quicksum(COI * quicksum(AIO[a,d] for d in D) + 
                                COR * quicksum(ARO[a,d] for d in D) + 
                                CPP * quicksum(AIA[a,d] for d in D) +
                                CPR * quicksum(ARA[a,d] for d in D) +
                                quicksum(CPAN[n] * quicksum(PAN[n,a,d] for d in D) + CRAN[n] * quicksum(RAN[n,a,d] for d in D) for n in N) +
                                quicksum(CPA[j] * quicksum(PA[j,a,d] for d in D) + CRA[j] * quicksum(RA[j,a,d] for d in D) for j in J) 
                                for a in A) <= PT), name="C17")

model.update()

# OBJECTIVE FUNCTION
FO = quicksum(quicksum(quicksum(R[a,h,d] for h in H) for d in D) for a in A)
model.setObjective(FO, GRB.MINIMIZE)

model.optimize()

model.printAttr('X')