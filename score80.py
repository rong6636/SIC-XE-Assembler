import json
import re
import os


class SICXE_Assembler():
    """
    Programmer: RONG ZHA WU

    SICXE
    THIS ASSEMBLER NOT INCLUDE "EQU USE ORG"

    """
    def __init__(self):
        """
        內部變數定義
        """
        self.__code_file = ""
        self.__SICXE_SET = []
        self.__code = []
        self.__symtab = {}
        self.__start = 0
        self.__length = 0
        self.__name = ""
        self.__machine_code = ""

    
    def load(self, code_file = "", set_file="SICXE_instruction_set.json"):
        self.__code_file = code_file
        self.__get_code_file(code_file)
        self.__get_SICXE_SET(set_file)
    
    def run(self):
        if len(self.__code) <= 0:
            print ("no code")
            return
        self.pass1()
        self.pass2()

    def pass1(self):
        """
        create LOC, SYMTAB
        """
        # START
        for iStart in range(len(self.__code)):
            if self.__code[iStart]["mnemonic"] == "START":
                self.__start = iStart
                self.__code[iStart]["Loc"] = hex(int(self.__code[iStart]["operand"], 16))[2:].zfill(6)
                self.__name = self.__code[iStart]["lable"]
                break

        loc = self.__code[self.__start]["Loc"]
        for i in range(iStart+1, len(self.__code)):
            # LOC
            mnemonic = self.__code[i]["mnemonic"]
            operand = self.__code[i]["operand"]

            # need to display Loc of mnemonic
            if mnemonic in self.__SICXE_SET["operand"] or mnemonic in self.__SICXE_SET["variable"] or mnemonic == "END" :
                self.__code[i]["Loc"] = loc[2:].zfill(6)  # Loc

                if mnemonic in self.__SICXE_SET["operand"]:
                    loc = hex(int(loc, 16) +
                                    self.__SICXE_SET["operand"][mnemonic][0])
                elif mnemonic in self.__SICXE_SET["variable"]:
                    if mnemonic == "RESW" or mnemonic == "RESB":
                        loc = hex(int(loc, 16) +
                                        self.__SICXE_SET["variable"][mnemonic]*int(operand))
                    elif mnemonic == "BYTE":
                        if operand[0] == 'C':
                            loc = hex(int(loc, 16) +
                                            self.__SICXE_SET["variable"][mnemonic]*(len(operand)-3))
                        elif operand[0] == 'X':
                            loc = hex(
                                int(loc, 16) + self.__SICXE_SET["variable"][mnemonic]*(int((len(operand)-2)/2)))
                    elif mnemonic == "WORD":
                        loc = hex(int(loc, 16) + 3)
            else:
                self.__code[i]["Loc"] = ""  # Loc

            # Symbol table
            lable = self.__code[i]["lable"]
            if lable != "":
                self.__symtab[lable] = self.__code[i]["Loc"]

    def pass2(self):
        """
        create object code
        create machine code
        """
        # object code
        base = self.__code[self.__start]["Loc"]
        pc = self.__code[self.__start]["Loc"]
        for indxe in range(len(self.__code)):
            if indxe < len(self.__code)-2:
                iNext = indxe+1
                while (self.__code[iNext]["Loc"] == ""):
                    if iNext > len(self.__code)-1:
                        break
                    iNext = iNext+1

            pc = self.__code[iNext]["Loc"]
            mnemonic = self.__code[indxe]["mnemonic"]
            operand = self.__code[indxe]["operand"]
            object_code = ""
            modification_record = 0

            # opcode - operand
            if mnemonic in self.__SICXE_SET["operand"]:
                opcode = bin(int(self.__SICXE_SET["operand"][mnemonic][1], 16))[2:]
                # format 3 or 4
                if self.__SICXE_SET["operand"][mnemonic][0] >= 3:
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
                        if self.__SICXE_SET["operand"][mnemonic][0] == 4:
                            e = 1

                        # b p and disp
                        if e == 0:
                            if operand_key in self.__symtab:
                                tmp_d = int(self.__symtab[operand_key], 16)-int(pc, 16)
                                p = 1
                                if tmp_d > 2047 or tmp_d < -2048:  # 超過PC能使用界線, 改用BASE做參考
                                    b = 1
                                    p = 0
                                    tmp_d = int(
                                        self.__symtab[operand_key], 16)-int(base, 16)
                                disp = hex(tmp_d)

                            else:  # may be is num
                                disp = hex(int(operand_key))
                                b = 0
                                p = 0
                        if e == 1:
                            if operand_key in self.__symtab:
                                disp = self.__symtab[operand_key]
                                modification_record = 5
                        object_code = hex(int(opcode, 2)+n*2+im)[2:].zfill(2)+hex(x*8+b*4+p*2+e)[2:]+self.__formatting_disp(disp, e)

                    else:
                        object_code = hex(int(opcode, 2)+n*2+im)[2:].zfill(2)+hex(x*8+b*4+p*2+e)[2:]+self.__formatting_disp(disp, e)
                elif self.__SICXE_SET["operand"][mnemonic][0] == 2:
                    r1 = operand.split(',')[0]
                    r2 = "A" # 預設 0 (A == 0)
                    if ',' in operand:
                        r2 = operand.split(',')[1]
                    object_code = hex(int(opcode, 2))[2:].zfill(2) + self.__SICXE_SET["register"][r1] + self.__SICXE_SET["register"][r2]
                

            if mnemonic == "BASE":
                base = self.__symtab[operand]
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

            self.__code[indxe]["object_code"] = object_code.upper()
            self.__code[indxe]["ob_len"] = len(self.__code[indxe]["object_code"])
            self.__code[indxe]["MR"] = modification_record

        # machine code
        self.__create_machine_code()

    def __get_code_file(self, code_file):
        f = None
        tmp_code=[]
        try:
            f = open(code_file, 'r')
            for line in f.readlines():
                item = re.split(r'\s+', line, 2)
                tmp_code.append(
                    {"lable": item[0], "mnemonic": item[1], "operand": item[2].strip()})
            self.__code = tmp_code
        except IOError:
            print('ERROR: can not found ' + code_file)
            if f:
                f.close()
        finally:
            if f:
                f.close()
    
    def __get_SICXE_SET(self, set_file):
        tmp_set = []
        try:
            with open(set_file, 'r', encoding='utf8') as jfile:
                tmp_set = json.load(jfile)
                jfile.close()
            self.__SICXE_SET = tmp_set
        except Exception as e:
            print('ERROR:  ' + str(e))
    
    def __formatting_disp(self, disp, e):
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

            
    def __create_machine_code(self, smb='^'):
        self.__length = int(self.__code[len(self.__code)-1]["Loc"], 16)-int(self.__code[self.__start]["Loc"], 16)
        
        # Header
        machine_code = "H"+smb
        machine_code += self.__name.ljust(6)
        machine_code += smb+self.__code[self.__start]["Loc"].zfill(6)
        machine_code += smb+hex(self.__length)[2:].zfill(6)+"\n"

        # Text record part
        tRecord = []
        newRow = True
        
        for i in range(len(self.__code)-1):
            i += 1
            loc = self.__code[i]["Loc"]
            mmn = self.__code[i]["mnemonic"]
            obc = self.__code[i]["object_code"]

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
                    tRecord[-1][2] += obc+smb
        for t in tRecord:
            machine_code += "T"+smb
            machine_code += t[0].zfill(6)+smb
            machine_code += hex(t[1])[2:].zfill(2)+smb
            machine_code += t[2][:-1]+"\n"

        
        # Modification record
        mRecord = []
        mc_count = 0
        for i in range(len(self.__code)-1):
            if self.__code[i]["MR"] > 0:
                start_loc = mc_count+(len(self.__code[i]["object_code"])-self.__code[i]["MR"])
                mRecord.append([start_loc//2, self.__code[i]["MR"]])
            mc_count+=len(self.__code[i]["object_code"])

        for m in mRecord:
            machine_code += "M"+smb
            machine_code += hex(m[0])[2:].zfill(6)+smb
            machine_code += hex(m[1])[2:].zfill(2)+"\n"
        
        # End
        machine_code += "E"+smb
        machine_code += self.__code[self.__start]["Loc"].zfill(6)
        machine_code+="\n\n\n"

        self.__machine_code = machine_code.upper()
        
    def cout(self):
        if len(self.__code) <= 0 :
            print ("no code ")
            return
        print ("SYMTAB\n===========\n", self.__symtab, "\n")
        print ("PROGRAM\n===========")
        for i in range(len(self.__code)):
            if self.__code[i]["mnemonic"] == "END": # 不顯示END的LOC
                print('%-7s' % "", end="")
            else:
                print('%-7s' % self.__code[i]["Loc"], end="")
            print('%-8s' % self.__code[i]["lable"], end="")
            print('%-7s' % self.__code[i]["mnemonic"], end="")
            print('%-11s' % self.__code[i]["operand"], end="")
            
            if "object_code" in self.__code[i]: # 沒object_code
                print('%-8s' % self.__code[i]["object_code"], end="")
            else:
                print('%-8s' % "", end="")
                
            # print('%2s' % self.__code[i]["ob_len"])
            print ("")
        print ("\nMACHINE CODE\n===========")
        print (self.__machine_code)
    
    def output_object_program(self):
        if not os.path.exists("./output"):
            os.makedirs("./output")
        path = "output/ob_"+os.path.basename(self.__code_file)
        f = open(path, 'w')
        f.write(self.__machine_code)
        f.close()
        
    def output_assembly_code(self):
        if not os.path.exists("./output"):
            print ("./output")
            os.makedirs("./output")
        path = "output/as_"+os.path.basename(self.__code_file)
        f = open(path, 'w')
        for i in range(len(self.__code)):
            if self.__code[i]["mnemonic"] == "END": # 不顯示END的LOC
                print('%-7s' % "", end="", file=f)
            else:
                print('%-7s' % self.__code[i]["Loc"], end="", file=f)
            print('%-8s' % self.__code[i]["lable"], end="", file=f)
            print('%-7s' % self.__code[i]["mnemonic"], end="", file=f)
            print('%-11s' % self.__code[i]["operand"], end="", file=f)
            
            if "object_code" in self.__code[i]: # 沒object_code
                print('%-8s' % self.__code[i]["object_code"], end="", file=f)
            else:
                print('%-8s' % "", end="", file=f)
                
            # print('%2s' % self.__code[i]["ob_len"])
            print ("", file=f)
        f.close()


        