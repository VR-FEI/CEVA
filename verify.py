import pandas as pd

codeTable = {}
codeTable['a'] = [10,30]
codeTable['b'] = [11,31]
codeTable['c'] = [12,32]
codeTable['d'] = [13,33]
codeTable['e'] = [14,34]
codeTable['f'] = [15,35]
codeTable['h'] = [16,36]
codeTable['j'] = [17,37]
codeTable['k'] = [18,38]
codeTable['l'] = [19,39]
codeTable['m'] = [20,40]
codeTable['n'] = [21,41]
codeTable['p'] = [22,42]
codeTable['r'] = [23,43]
codeTable['t'] = [24,44]
codeTable['u'] = [25,45]
codeTable['v'] = [26,46]
codeTable['w'] = [27,47]
codeTable['x'] = [28,48]
codeTable['y'] = [29,49]

def SKUletra(letra, aux):
    if letra in codeTable:
        SKUnovo = codeTable[letra][aux]
    else:
        SKUnovo = "00"

    return SKUnovo

def verify(SKU):
    SKU = SKU.lower()
    if len(SKU) != 4:
        rec = "SKU inválido "
        desc = fam = "*"
    else:
        aux0 = SKU[0].isnumeric()
        aux1 = SKU[1].isnumeric()
        aux2 = SKU[2].isnumeric()
        aux3 = SKU[3].isnumeric()

        if not (aux0 or aux3) or (not aux1) or (not aux2):
            SKUnum = SKUnovo = ''
        elif aux0 and aux3:
            SKUnum = ''
            SKUnovo = SKU
        elif aux3:
            SKUnum = SKU[1] + SKU[2] + SKU[3]
            SKUnovo = SKUletra(SKU[0], 0)
        else:
            SKUnum = SKU[0] + SKU[1] + SKU[2]
            SKUnovo = SKUletra(SKU[3], 1)

        #SKUnovo = str(SKUnovo) + SKUnum + "00"
        SKUnovo = str(SKUnovo) + SKUnum

        #print("A", SKUnovo)
        df = pd.read_csv("./Data/SKU.csv")
        #df["ENCONTRADO"] = df.apply(lambda x: int(SKUnovo) in x.values, axis=1)
        df["ENCONTRADO"] = df.apply(lambda x: any(str(val).startswith(str(SKUnovo)) for val in x.values), axis=1)
        df = df.query("ENCONTRADO == True")
        #print(df[df["ENCONTRADO"] == True])
        df = df.head(1)
        if df.empty or SKUnovo == "":
            rec = "SKU não reconhecido "
            desc = fam = "*"
        else:
            rec = "SKU reconhecido: "
            desc = df["DESCRIÇÃO "].to_string(header = False, index = False)
            fam = df["FAMILIA "].to_string(header = False, index = False)

    return rec, desc, fam
