import re
import json


def get_SIC_instruction_set():
    with open('SIC_instruction_set.json', 'r', encoding='utf8') as jfile:
        SIC_instruction_set = json.load(jfile)
        jfile.close()
    return SIC_instruction_set


def get_SIC_from_file(input_path="Figure2.15.txt"):
    f = None
    sic = []
    try:
        f = open(input_path, 'r')
        for line in f.readlines():
            item = re.split(r'\s+', line, 2)
            if len(item) > 2:
                sic.append({"lable":item[0], "mnemonic":item[1], "operand":item[2].strip()})
    except IOError:
        print('ERROR: can not found ' + input_path)
        if f:
            f.close()
    finally:
        if f:
            f.close()
    return sic


sic = get_SIC_from_file()

for i in range(len(sic)):
    print(sic[i])

SIC_SET = get_SIC_instruction_set()
print(len(SIC_SET["operand"]))

programCode = sic

# # create Line
# for i in range(len(programCode)):
#     programCode[i].insert(0, (i+1)*5)

# create block table
current_block = 0  # init current_block
block_table = {
    "": {
        "number": 0,
        "address": "",
        "length": "0x0"
    }
}

# create LOC
current_Loc = hex(0)  # init current_Loc
for i in range(len(programCode)):
    if programCode[i]["mnemonic"]=="START":
        current_Loc = hex(int(programCode[i]["operand"], 16))
        break

for i in range(len(programCode)):
    mnemonic = programCode[i]["mnemonic"]
    operand = programCode[i]["operand"]

    print (mnemonic, operand)
    if mnemonic == "USE":
        # store current block
        block_table[operand]["length"] = hex(int(current_Loc, 16) - int(block_table[operand]["address"], 16))
        if operand not in block_table:
            block_table[operand] = {
                "number": len(block_table),
                "address": current_Loc,
                "length": "0x0"
            }

    programCode[i]["Loc"] = current_Loc # Loc
    programCode[i]["block"] = current_block # block


    if mnemonic in SIC_SET["operand"]:
        current_Loc = hex(int(current_Loc, 16)+SIC_SET["operand"][mnemonic][0])
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
            current_Loc = hex(int(current_Loc, 16) + SIC_SET["variable"][mnemonic])

for i in range(len(programCode)):
    print(programCode[i]["Loc"], programCode[i]["mnemonic"], programCode[i]["operand"])
