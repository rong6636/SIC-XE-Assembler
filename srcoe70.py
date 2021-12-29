from os import makedirs, system
import re
import json


def read_SICXE_instruction_set():
    with open('SICXE_instruction_set.json', 'r', encoding='utf8') as jfile:
        SIC_instruction_set = json.load(jfile)
        jfile.close()
    return SIC_instruction_set


def read_assembly_code_file(input_path="Figure2.5.txt"):
    f = None
    ass = []
    try:
        f = open(input_path, 'r')
        for line in f.readlines():
            item = re.split(r'\s+', line, 2)
            ass.append(
                {"lable": item[0], "mnemonic": item[1], "operand": item[2].strip()})
    except IOError:
        print('ERROR: can not found ' + input_path)
        if f:
            f.close()
    finally:
        if f:
            f.close()
    return ass

# create LOC

def formatting_Loc(loc):
    _loc = loc[2:]
    while(len(_loc)<4):
        _loc = "0"+_loc
    return _loc.upper()

def create_Loc(sic):
    current_Loc = hex(0)  # init current_Loc
    for iStart in range(len(sic)):
        if sic[iStart]["mnemonic"] == "START":
            current_Loc = hex(int(sic[iStart]["operand"], 16))
            sic[iStart]["Loc"] = formatting_Loc(current_Loc)
            break

    for i in range(iStart+1, len(sic)):
        mnemonic = sic[i]["mnemonic"]
        operand = sic[i]["operand"]

        # need to display Loc of mnemonic
        if mnemonic in SIC_SET["operand"] or mnemonic in SIC_SET["variable"] or mnemonic == "END" :
            sic[i]["Loc"] = formatting_Loc(current_Loc)  # Loc

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
        modification_record = 0

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
                operand_key = operand
                if len(operand) > 0:
                    # n i
                    if operand[0] == "@":
                        n = 1
                        im = 0
                        operand_key = operand_key[1:]
                    elif operand[0] == "#":
                        n = 0
                        im = 1
                        operand_key = operand_key[1:]
                    # x
                    if "," in operand:
                        x = 1
                        operand_key = operand_key[:operand_key.find(",")]
                    # e
                    if SIC_SET["operand"][mnemonic][0] == 4:
                        e = 1

                    # b p and disp
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
                            modification_record = 5

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
            print("BASE====", base)

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
            object_code = hex(int(operand))[2:].zfill(6)

        sic[i]["object_code"] = object_code.upper()
        sic[i]["ob_len"] = len(sic[i]["object_code"])
        sic[i]["MR"] = modification_record
        print("--------")
    return sic

# def get_machine_code(sic, symbol=''):
#     r=0
#     while r<len(sic):
#         if sic[r]["Loc"] == "":
#             sic.pop(r)
#             r = -1
#         r+=1
#     machine_code = ""
#     # Header part
#     for iSTART in range(len(sic)): # find "START"
#         if sic[iSTART]["mnemonic"] == "START":
#             machine_code += "H"+symbol # 1 Header
#             machine_code += sic[iSTART]["lable"].ljust(6)+symbol  # 2-7 program name 
#             machine_code += sic[iSTART]["Loc"].zfill(6)+symbol # 8-13 start loc
#             _len = str(int(sic[len(sic)-1]["Loc"], 16)-int(sic[iSTART]["Loc"], 16))
#             machine_code += _len.zfill(6)+"\n" # 14-19 length
#             break
#     # Text part
#     i = iSTART
#     tmp_start_loc = sic[iSTART]["Loc"]
#     tmp_mCode = ""
#     while (i<len(sic)-1):
#         i+=1
#         print (sic[i])
#         # 若tmp+object_code 長度大於60
#         if len(tmp_mCode+sic[i]["object_code"])>60 or :
#             print ("tmp", tmp_mCode)
#             machine_code += "T"+symbol
#             machine_code += tmp_start_loc.zfill(6)+symbol # start loc
#             print (sic[i-1]["Loc"])
#             print (int(sic[i-1]["Loc"], 16))
#             print (int(tmp_start_loc, 16))
#             machine_code += hex(len(tmp_mCode))[2:].zfill(2)+symbol # start loc
#             machine_code += tmp_mCode+"\n"

#             # zeoring
#             tmp_start_loc = sic[i]["Loc"]
#             tmp_mCode = sic[i]["object_code"]
#         else:
#             tmp_mCode = tmp_mCode+sic[i]["object_code"]

#     # End part
#     machine_code += "E"+sic[iSTART]["Loc"].zfill(6) # 14-19 length
        
#     return machine_code

def get_machine_code(sic, smb='^'):

    # Header record part
    program_name = ""
    program_startLoc = ""
    program_len = ""
    for iSTART in range(len(sic)):
        # find "START"
        if sic[iSTART]["mnemonic"] == "START":
            program_name = sic[iSTART]["lable"]
            program_startLoc = sic[iSTART]["Loc"]
            program_len = int(sic[len(sic)-1]["Loc"], 16)-int(sic[iSTART]["Loc"], 16)
            break
    
    # Text record part
    tRecord = []
    newRow = True
    
    for i in range(len(sic)-1):
        i += 1
        loc = sic[i]["Loc"]
        mmn = sic[i]["mnemonic"]
        obc = sic[i]["object_code"]

        if mmn == 'RESW' or mmn == 'RESB':
            # RESW, RESB interrupt continuous address.
            newRow = True
        if obc != '':
            if newRow:
                # [起始位置,  長度, CODE]
                tRecord.append([loc, 0, ""])
                newRow = False

            if tRecord[-1][1]*2+len(obc) > 60:
                tRecord.append([loc, len(obc)//2, obc])
            else:
                tRecord[-1][1] += len(obc)//2
                tRecord[-1][2] += smb+obc
    
    # Modification record
    mRecord = []
    mc_count = 0
    for i in range(len(sic)-1):
        if sic[i]["MR"] > 0:
            start_loc = mc_count+(len(sic[i]["object_code"])-sic[i]["MR"])
            mRecord.append([start_loc//2, sic[i]["MR"]])
        mc_count+=len(sic[i]["object_code"])


    
    # machine code
    machine_code = "H"+smb
    machine_code += program_name.ljust(6)
    machine_code += smb+program_startLoc.zfill(6)
    machine_code += smb+hex(program_len)[2:].zfill(6)+"\n"

    for t in tRecord:
        machine_code += "T"+smb
        machine_code += t[0].zfill(6)+smb
        machine_code += hex(t[1])[2:].zfill(2)+smb
        machine_code += t[2]+"\n"

    for m in mRecord:
        machine_code += "M"+smb
        machine_code += hex(m[0])[2:].zfill(6)+smb
        machine_code += hex(m[1])[2:].zfill(2)+"\n"

    machine_code += "E"+smb
    machine_code += program_startLoc.zfill(6)
    machine_code+="\n\n\n"

    return machine_code


sic = read_assembly_code_file()

# for i in range(len(sic)):
#     print(sic[i])

SIC_SET = read_SICXE_instruction_set()
# print(len(SIC_SET["operand"]))

sic = create_Loc(sic)
symtab = create_symtab(sic)
sic = create_object_code(sic)


for i in range(len(sic)):
    if sic[i]["mnemonic"] == "END": # 不顯示END的LOC
        print('%5s' % "", end="")
    else:
        print('%5s' % sic[i]["Loc"], end="")
    print('%7s' % sic[i]["lable"], end="")
    print('%7s' % sic[i]["mnemonic"], end="")
    print('%14s' % sic[i]["operand"], end="")
    print('%10s' % sic[i]["object_code"], end="")
    print('%2s' % sic[i]["ob_len"])

print (get_machine_code(sic))
