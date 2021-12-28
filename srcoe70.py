from os import system
import re
import json


def get_SIC_instruction_set():
    with open('SIC_instruction_set.json', 'r', encoding='utf8') as jfile:
        SIC_instruction_set = json.load(jfile)
        jfile.close()
    return SIC_instruction_set


def get_SIC_from_file(input_path="Figure2.5.txt"):
    f = None
    sic = []
    try:
        f = open(input_path, 'r')
        for line in f.readlines():
            item = re.split(r'\s+', line, 2)
            sic.append(
                {"lable": item[0], "mnemonic": item[1], "operand": item[2].strip()})
    except IOError:
        print('ERROR: can not found ' + input_path)
        if f:
            f.close()
    finally:
        if f:
            f.close()
    return sic

# create LOC

def format_Loc(loc):
    _loc = loc[2:]
    while(len(_loc)<4):
        _loc = "0"+_loc
    return _loc.upper()

def create_Loc(sic):
    current_Loc = hex(0)  # init current_Loc
    for iStart in range(len(sic)):
        if sic[iStart]["mnemonic"] == "START":
            current_Loc = hex(int(sic[iStart]["operand"], 16))
            sic[iStart]["Loc"] = format_Loc(current_Loc)
            break

    for i in range(iStart+1, len(sic)):
        mnemonic = sic[i]["mnemonic"]
        operand = sic[i]["operand"]

        # need to display Loc of mnemonic
        if mnemonic in SIC_SET["operand"] or mnemonic in SIC_SET["variable"] or mnemonic == "END" :
            sic[i]["Loc"] = format_Loc(current_Loc)  # Loc

            if mnemonic in SIC_SET["operand"]:
                current_Loc = hex(int(current_Loc, 16) +
                                  SIC_SET["operand"][mnemonic][0])
            elif mnemonic in SIC_SET["variable"]:
                if mnemonic == "RESW" or mnemonic == "RESB":
                    current_Loc = hex(int(current_Loc, 16) +
                                      SIC_SET["variable"][mnemonic]*int(operand))
                elif mnemonic == "BYTE":
                    if operand[0] == 'C':
                        current_Loc = hex(int(current_Loc, 16) +
                                          SIC_SET["variable"][mnemonic]*(len(operand)-3))
                    elif operand[0] == 'X':
                        current_Loc = hex(
                            int(current_Loc, 16) + SIC_SET["variable"][mnemonic]*(int((len(operand)-2)/2)))
                elif mnemonic == "WORD":
                    # current_Loc = hex(int(current_Loc, 16) +
                    #                   SIC_SET["variable"][mnemonic])
                    current_Loc = hex(int(current_Loc, 16) + 3)
        else:
            sic[i]["Loc"] = ""  # Loc
    return sic


def create_symtab(sic):
    symtab = {}
    for s in sic:
        if len(s["lable"]) > 0:
            symtab[s["lable"]] = s["Loc"]
    print("==================\n", symtab, "\n=====================")
    return symtab


def format_disp(disp, e):
    num = disp[2:]
    sign = "0"
    if disp[0] == "-":
        sign = "1"
        num = disp[3:]
    # 正號
    _bin = bin(int(num, 16))[2:]
    # 負號
    if disp[0] == "-":
        tmp = ""
        # 轉補數
        for i in bin(int(num, 16) - 1)[2:]:
            if i == "0":
                tmp = tmp + "1"
            else:
                tmp = tmp + "0"
        _bin = tmp

    _hex = ""
    # format 4
    if e == 1:
        while (len(_bin) < 20):
            _bin = sign + _bin
        _hex = hex(int(_bin, 2))[2:]
        while (len(_hex) < 5):
            _hex = "0"+_hex
    # format 3
    else:
        while (len(_bin) < 12):
            _bin = sign + _bin
        _hex = hex(int(_bin, 2))[2:]
        while (len(_hex) < 3):
            _hex = "0"+_hex

    return _hex


def format_opcode_ni(op):
    print("op"+op)
    op = op[2:]
    while (len(op) < 2):
        op = "0"+op
    return op

def create_object_code(sic):
    base = sic[0]["Loc"]
    pc = sic[0]["Loc"]
    for i in range(len(sic)):
        if i < len(sic)-2:
            si = i+1
            while (sic[si]["Loc"] == ""):
                if si > len(sic)-1:
                    break
                si = si+1
        print(i, si)
        pc = sic[si]["Loc"]
        mnemonic = sic[i]["mnemonic"]
        operand = sic[i]["operand"]
        object_code = ""

        # opcode - operand
        if mnemonic in SIC_SET["operand"]:
            print(mnemonic+"(" + SIC_SET["operand"]
                  [mnemonic][1][2:]+")", operand)
            opcode = bin(int(SIC_SET["operand"][mnemonic][1], 16))[2:]
            # format 3 or 4
            if SIC_SET["operand"][mnemonic][0] >= 3:
                # n i x b p e
                n = 1
                im = 1
                x = 0
                b = 0
                p = 0
                e = 0
                disp = "0x0"
                if len(operand) > 0:
                    # n i
                    if operand[0] == "@":
                        n = 1
                        im = 0
                    elif operand[0] == "#":
                        n = 0
                        im = 1
                    # x
                    if "," in operand:
                        x = 1
                    # e
                    if SIC_SET["operand"][mnemonic][0] == 4:
                        e = 1
                    # b p and disp
                    operand_key = operand
                    if x == 1:
                        operand_key = operand_key[:operand_key.find(",")]
                    if operand[0] in ["#", "@"]:
                        operand_key = operand_key[1:]
                    if e == 0:
                        if operand_key in symtab:
                            print("symtab[operand_key]", symtab[operand_key])
                            print("pc", pc)
                            tmp_d = int(symtab[operand_key], 16)-int(pc, 16)
                            p = 1
                            if tmp_d > 2047 or tmp_d < -2048:  # 超過PC能使用界線, 改用BASE做參考
                                b = 1
                                p = 0
                                tmp_d = int(
                                    symtab[operand_key], 16)-int(base, 16)
                            disp = hex(tmp_d)

                        else:  # may be is num
                            disp = hex(int(operand_key))
                            b = 0
                            p = 0
                    if e == 1:
                        if operand_key in symtab:
                            disp = symtab[operand_key]

                    print(opcode, n, im, x, b, p, e, bin(int(disp, 16))[2:])
                    object_code = format_opcode_ni(
                        hex(int(opcode, 2)+n*2+im))+hex(x*8+b*4+p*2+e)[2:]+format_disp(disp, e)

                else:
                    print("operand == \"\"")
                    print(opcode, n, im, x, b, p, e, bin(int(disp, 16))[2:])
                    object_code = format_opcode_ni(
                        hex(int(opcode, 2)+n*2+im))+hex(x*8+b*4+p*2+e)[2:]+format_disp(disp, e)
            elif SIC_SET["operand"][mnemonic][0] == 2:
                print("format 2")
                r1 = operand.split(',')[0]
                r2 = "A" # 預設 0 (A == 0)
                if ',' in operand:
                    r2 = operand.split(',')[1]
                object_code = format_opcode_ni(hex(int(opcode, 2))) + SIC_SET["register"][r1] + SIC_SET["register"][r2]
            print(object_code.upper())

        if mnemonic == "BASE":
            base = symtab[operand]
            print("BASE", base)

        # opcode - variable
        elif mnemonic == "BYTE":
            if operand[0] == 'C':
                tmp = 0
                for o in operand[2:-1]:
                    tmp = tmp*256+ord(o)
                object_code = hex(tmp)[2:]
            elif operand[0] == 'X':
                object_code = operand[2:-1]
        elif mnemonic == "WORD":
            object_code = hex(int(operand))[2:]

        sic[i]["object_code"] = object_code.upper()
        print("--------")
    return sic

def create_object_program(sic):
    opContain = ""
    # Header part
    for iSTART in range(len(sic)): # find "START"
        if sic[iSTART]["mnemonic"] == "START":
            opContain += "H" # 1 Header
            opContain += sic[iSTART]["lable"].ljust(6) # 2-7 program name 
            opContain += sic[iSTART]["Loc"].ljust(6) # 8-13 program name 
            sic[len(sic)]["Loc"]-sic[iSTART]["Loc"]
            opContain += sic[iSTART]["Loc"].ljust(6) # 14-19 length
            break
    return opContain

sic = get_SIC_from_file()

# for i in range(len(sic)):
#     print(sic[i])

SIC_SET = get_SIC_instruction_set()
# print(len(SIC_SET["operand"]))

sic = create_Loc(sic)
symtab = create_symtab(sic)
sic = create_object_code(sic)

for i in range(len(sic)):
    if sic[i]["mnemonic"] != "END": # 不顯示END的LOC
        print('%5s' % sic[i]["Loc"], end="")
    print('%7s' % sic[i]["lable"], end="")
    print('%7s' % sic[i]["mnemonic"], end="")
    print('%14s' % sic[i]["operand"], end="")
    print('%10s' % sic[i]["object_code"])

# object_program = create_object_program(sic)
