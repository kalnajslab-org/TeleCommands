import PySimpleGUIQt as sg  
import csv
import time

tc_filename = 'TC_Parameters.csv'
Font = ('Courier', 16)

def read_parameter_file(filename,Instrument):
    ''' This reads the csv file and returns each column as a list '''
    Parameter = []
    Enum = []
    Default =[]
    Values = []
    Max = []
    Min = []
    Notes = []
    
    with open(filename, mode='r', encoding="utf8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if row['Instrument'] == Instrument:

                Parameter.append(row["Parameter"])
                Enum.append(int(row["Enum"]))
                Values.append(int(row["Values"]))
                Default.append(float(row["Default"]))
                Min.append(float(row["Min_val"]))
                Max.append(float(row["Max_val"]))
                Notes.append(row["Notes"])
#                print(f'\t{row["Parameter"]} is accesed through Enum {row["Enum"]}, and has default value {row["Default"]} and is used to {row["Notes"]}.')
                line_count += 1
        print(f'Processed {line_count} lines.') 
        
        #add a blank entry at the end for the GUI
        Parameter.append("")
        Enum.append("")
        Values.append("")
        Default.append("")
        Min.append("")
        Max.append("")
        Notes.append("")
    return Parameter, Enum, Default, Values,Max, Min, Notes
        

def crc16_ccitt(crc, data):
    msb = crc >> 8
    lsb = crc & 255

    for c in data:
        x = c ^ msb
        x ^= (x >> 4)
        msb = (lsb ^ (x >> 3) ^ (x << 4)) & 255
        lsb = (x ^ (x << 5)) & 255
    return (msb << 8) + lsb


def MakeTCFile(filename, command):
    ''' Generates the TC file and adds the CRC'''
    start = 'START'
    end = 'END'
    TCfile = open(filename,"wb")
    TCByteList = command.encode("ASCII")
    calc_crc = crc16_ccitt(0x1021, TCByteList)

    TCfile.write(start.encode())
    TCfile.write(command.encode())
    TCfile.write(calc_crc.to_bytes(2, byteorder='big', signed=False))
    TCfile.write(end.encode())

def pick_an_instrument():
    ''' Select the instrument to generate TC files for'''

    instruments = ['LPC','RACHuTS','FLOATS']
    
    instrument_layout = [[sg.InputCombo(values=instruments, key = '_inst_',  font = Font)]]
    layout_pick_instrument = [[sg.Frame('Select Instrument: ', instrument_layout, font = Font)],
                        [sg.Submit( font = Font), sg.Cancel( font = Font)]]

    instrument_window = sg.Window('Select Instrument', layout_pick_instrument)
    event, values = instrument_window.Read()
    instrument_window.Close()

    if event is None or event == 'Cancel':
        return None
    if event == 'Submit':
        print(values['_inst_'])
        return values['_inst_']

def pick_a_TC(instrument):
    ''' Graphical User interface - prompts the user for instrument, command and value
        then calls MakeTCfile to assemble the TC file based on the users choices '''
    params, enums, defaults, num_vals,val_max, val_min, notes = read_parameter_file(tc_filename,instrument)
    param_layout = [[sg.Listbox(values=params,key = '_param_', tooltip = 'Select command to send', size=(20, 6),font = Font)]]
    #param_layout = [[sg.InputCombo(values=params, key = '_param_',  font = Font)]]
    

    layout_pick_parameter = [[sg.Frame('Select Parameter to Update: ', param_layout, font = Font)],
                             #[sg.Frame('Input new value: ', value_layout, font = Font)],
                             [sg.Submit( font = Font), sg.Cancel( font = Font)]]
                             
    

    param_window = sg.Window('Select Parameter', layout_pick_parameter)
    event, values = param_window.Read()
    param_window.Close()
    
    tcString = values['_param_'][0]
    print(tcString)
    
    indx = 0
    enumeration = 999
    for words in params:
        if words == tcString:
            enumeration = enums[indx]
            break
        else:
            indx += 1

    if num_vals[indx] == 0:
        confirm_layout = [[sg.Text('Confirm: ' + notes[indx],font = Font)],
                          [sg.Submit(), sg.Cancel()]]
        confirm_window = sg.Window('Confirm Command',confirm_layout)
        
        event, values = confirm_window.Read()
        confirm_window.Close()

        if event is None or event == 'Cancel':
            return None, None
        if event == 'Submit':
            filename = instrument+time.strftime("%Y%m%d-%H%M%S")+'.tc'
            cmnd = str(enumeration) + ';'
            MakeTCFile(filename, cmnd)
            sg.Popup('Command is Valid \nWriting ' + cmnd + '\nTo '+ instrument + ' TC file: ' + filename,font = Font)
            return True, 0


    if num_vals[indx] == 1:
        value_layout =  [[sg.Text(notes[indx],font = Font)],
                     [sg.Text('Default Value '+ str(defaults[indx]),font = Font)],
                        [sg.Text('Value:',font = Font), sg.InputText( key = '_val_')]]
        layout_enter_value = [[sg.Frame('Input new value: ', value_layout, font = Font)],
                              [sg.Submit( font = Font), sg.Cancel( font = Font)]]
        
        value_window = sg.Window('Enter Value',layout_enter_value)
        event, values = value_window.Read()
        value_window.Close()

        new_param_value = float(values['_val_'])
        print(new_param_value)

        if new_param_value < float(val_max[indx]) and new_param_value > float(val_min[indx]):
            print('New value is within range')
        else:
            sg.Popup('Value(s) out of Range!\nNo TC File Created',font = Font)
            print('New Value out of Range!')
            return 'error', 0

        filename = instrument+time.strftime("%Y%m%d-%H%M%S")+'.tc'
        cmnd = str(enumeration)+',' + str(new_param_value) +';'
        MakeTCFile(filename,cmnd)
        sg.Popup('Values within range \nWriting ' + cmnd + '\nTo: ' + instrument + ' TC file: ' + filename,font = Font)
        return True, 1

    if num_vals[indx] == 2:
        value_layout =  [[sg.Text(notes[indx],font = Font)],
                         [sg.Text('Default Value '+ str(defaults[indx])+ 'No Limit Checking for values!',font = Font)],
                         [sg.Text('Value 1:',font = Font), sg.InputText( key = '_val1_')],
                         [sg.Text('Value 2:',font = Font), sg.InputText( key = '_val2_')]]


        layout_enter_value = [[sg.Frame('Input new value: ', value_layout, font = Font)],
                               [sg.Submit( font = Font), sg.Cancel( font = Font)]]
                         
        value_window = sg.Window('Enter Value',layout_enter_value)
        event, values = value_window.Read()
        value_window.Close()

        new_param_value_1 = float(values['_val1_'])
        new_param_value_2 = float(values['_val2_'])

        if new_param_value_1 < int(val_max[indx]) and new_param_value_1 > int(val_min[indx]):
            print('Value one is within range')
        if new_param_value_2 < int(val_max[indx]) and new_param_value_2 > int(val_min[indx]):
            print('Value two is within range')
        else:
            sg.Popup('Value(s) out of Range!\nNo TC File Created',font = Font)
            print('Value out of Range!')
            return 'error', 0

        filename = instrument+time.strftime("%Y%m%d-%H%M%S")+'.tc'
        cmnd = str(enumeration)+',' + str(new_param_value_1) + ',' + str(new_param_value_2) + ';'
        MakeTCFile(filename,cmnd)
        sg.Popup('Values within range \nWriting ' + cmnd + '\nTo: ' + instrument + ' TC file: ' + filename,font = Font)
        return True, 2

    if num_vals[indx] == 3:
        value_layout =  [[sg.Text(notes[indx],font = Font)],
                     [sg.Text('Default Value '+ str(defaults[indx])+ 'No Limit Checking for values!',font = Font)],
                     [sg.Text('Value 1:',font = Font), sg.InputText( key = '_val1_')],
                     [sg.Text('Value 2:',font = Font), sg.InputText( key = '_val2_')],
                     [sg.Text('Value 3:',font = Font), sg.InputText( key = '_val3_')]]
                     
        layout_enter_value = [[sg.Frame('Input new value: ', value_layout, font = Font)],
                              [sg.Submit( font = Font), sg.Cancel( font = Font)]]
            
        value_window = sg.Window('Enter Value',layout_enter_value)
        event, values = value_window.Read()
        value_window.Close()

        new_param_value_1 = int(values['_val1_'])
        new_param_value_2 = int(values['_val2_'])
        new_param_value_3 = int(values['_val3_'])

        if new_param_value_1 < int(val_max[indx]) and new_param_value_1 > int(val_min[indx]):
          print('Value one is within range')
        if new_param_value_2 < int(val_max[indx]) and new_param_value_2 > int(val_min[indx]):
            print('Value two is within range')
        if new_param_value_3 < int(val_max[indx]) and new_param_value_3 > int(val_min[indx]):
            print('Value three is within range')
        else:
            sg.Popup('Value(s) out of Range!\nNo TC File Created',font = Font)
            print('Value out of Range!')
            return 'error', 0
        
        filename = instrument+time.strftime("%Y%m%d-%H%M%S")+'.tc'
        cmnd = str(enumeration)+',' + str(new_param_value_1) + ',' + str(new_param_value_2) + ',' + str(new_param_value_3) + ';'
        MakeTCFile(filename,cmnd)
        sg.Popup('Values within range \nWriting ' + cmnd + '\nTo: ' + instrument + ' TC file: ' + filename,font = Font)
        return True, 3

    if num_vals[indx] == 4:
        value_layout =  [[sg.Text(notes[indx],font = Font)],
                     [sg.Text('Default Value '+ str(defaults[indx])+ 'No Limit Checking for values!',font = Font)],
                     [sg.Text('Value 1:',font = Font), sg.InputText( key = '_val1_')],
                     [sg.Text('Value 2:',font = Font), sg.InputText( key = '_val2_')],
                     [sg.Text('Value 3:',font = Font), sg.InputText( key = '_val3_')],
                     [sg.Text('Value 4:',font = Font), sg.InputText( key = '_val4_')]]
        
        layout_enter_value = [[sg.Frame('Input new value: ', value_layout, font = Font)],
                     [sg.Submit( font = Font), sg.Cancel( font = Font)]]
                         
        value_window = sg.Window('Enter Value',layout_enter_value)
        event, values = value_window.Read()
        value_window.Close()

        new_param_value_1 = int(values['_val1_'])
        new_param_value_2 = int(values['_val2_'])
        new_param_value_3 = int(values['_val3_'])
        new_param_value_4 = int(values['_val4_'])

        if new_param_value_1 < int(val_max[indx]) and new_param_value_1 > int(val_min[indx]):
            print('Value one is within range')
        if new_param_value_2 < int(val_max[indx]) and new_param_value_2 > int(val_min[indx]):
            print('Value two is within range')
        if new_param_value_3 < int(val_max[indx]) and new_param_value_4 > int(val_min[indx]):
            print('Value three is within range')
        if new_param_value_4 < int(val_max[indx]) and new_param_value_3 > int(val_min[indx]):
            print('Value four is within range')
        else:
            sg.Popup('Value(s) out of Range!\nNo TC File Created',font = Font)
            print('Value out of Range!')
            return False, 0

        filename = instrument+time.strftime("%Y%m%d-%H%M%S")+'.tc'
        cmnd = str(enumeration)+',' + str(new_param_value_1) + ',' + str(new_param_value_2) + ',' + str(new_param_value_3)+ ',' + str(new_param_value_4) + ';'
        MakeTCFile(filename,cmnd)
        sg.Popup('Values within range \nWriting ' + cmnd + '\nTo: ' + instrument + ' TC file: ' + filename,font = Font)
        return True, 4
                 
    if num_vals[indx] == 5:
        value_layout =  [[sg.Text(notes[indx],font = Font)],
                 [sg.Text('Default Value '+ str(defaults[indx])+ 'No Limit Checking for values!',font = Font)],
                 [sg.Text('Value 1:',font = Font), sg.InputText( key = '_val1_')],
                 [sg.Text('Value 2:',font = Font), sg.InputText( key = '_val2_')],
                 [sg.Text('Value 3:',font = Font), sg.InputText( key = '_val3_')],
                 [sg.Text('Value 4:',font = Font), sg.InputText( key = '_val4_')],
                 [sg.Text('Value 5:',font = Font), sg.InputText( key = '_val5_')]]

        layout_enter_value = [[sg.Frame('Input new value: ', value_layout, font = Font)],
                           [sg.Submit( font = Font), sg.Cancel( font = Font)]]
                     
        value_window = sg.Window('Enter Value',layout_enter_value)
        event, values = value_window.Read()
        value_window.Close()

        new_param_value_1 = int(values['_val1_'])
        new_param_value_2 = int(values['_val2_'])
        new_param_value_3 = int(values['_val3_'])
        new_param_value_4 = int(values['_val4_'])
        new_param_value_5 = int(values['_val5_'])

        if new_param_value_1 < int(val_max[indx]) and new_param_value_1 > int(val_min[indx]):
         print('Value one is within range')
        if new_param_value_2 < int(val_max[indx]) and new_param_value_2 > int(val_min[indx]):
         print('Value two is within range')
        if new_param_value_3 < int(val_max[indx]) and new_param_value_3 > int(val_min[indx]):
         print('Value three is within range')
        if new_param_value_4 < int(val_max[indx]) and new_param_value_4 > int(val_min[indx]):
         print('Value four is within range')
        if new_param_value_5 < int(val_max[indx]) and new_param_value_5 > int(val_min[indx]):
         print('Value four is within range')
        else:
            sg.Popup('Value(s) out of Range!\nNo TC File Created',font = Font)
            print('Value out of Range!')
            return False, 0
        
        filename = instrument+time.strftime("%Y%m%d-%H%M%S")+'.tc'
        cmnd = str(enumeration)+',' + str(new_param_value_1) + ',' + str(new_param_value_2) + ',' + str(new_param_value_3)+','  + str(new_param_value_4) +',' + str(new_param_value_5) + ';'
        MakeTCFile(filename,cmnd)
        sg.Popup('Values within range \nWriting ' + cmnd + '\nTo: ' + instrument + ' TC file: ' + filename,font = Font)
        return True, 5

    
instrument = pick_an_instrument()
param, num_vals = pick_a_TC(instrument)



         

