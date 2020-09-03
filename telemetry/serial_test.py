import serial
​
# COM3 : left USB2.0 on left side
# \r   : carriage return escape character
# b''  : converts stying to byte literal
​
ser = serial.Serial('COM3')
​
if not ser.is_open:
	ser.open()
	print(ser.name, 'opened.')
	
if ser.is_open:
	command = b'TM\r' # requests current UT date/time
	bytes_written = ser.write(command)
	bytes_recieved = ser.in_waiting
	print(ser.read(bytes_recieved))
	
	ser.close()
	print(ser.name, 'closed.')
