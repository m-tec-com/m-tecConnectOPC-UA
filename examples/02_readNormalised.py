from opcua import Client, ua      

# connect
reader = Client("opc.tcp://10.129.4.73:4840")
reader.connect()
reader.load_type_definitions()

# read variable
node = reader.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.reserve_AI_2")
print("Temperature:", node.get_value()/10000*100)

# Sensor: 0°C - 100°C
# Analog: 0V  - 10V
# Value:  0   - 10000