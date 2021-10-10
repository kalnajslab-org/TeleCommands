# TeleCommands
Python code to generate TCs for LPC/RACHuTS/FLOATS on Strateole 2

This code generates ascii telecommands (TCs) to control the LASP FLOATS/RACHuTS/LPC instruments in flight.    The database of available TCs is stored in the TC_Parameters.csv file.   This includes the TC name, the TC code (a uint_8t) and description of the command and some rudimentry limit checking.  It is GUI based and will guide the user through selecting a TC, the required parameters for that TC, and will generate a binary TC file that can be sent throught the CCMz.  The beta version includes direct sending of TCs from within the app.  It requires the PySimpleGuiQt package to generate the GUI. 
