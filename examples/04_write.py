from opcua import Client, ua      

# connect
writer = Client("opc.tcp://10.129.4.73:4840")
writer.connect()
writer.load_type_definitions()

Livebit2DuoMix = writer.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.reserve_DO_1")
Livebit2DuoMix.set_value(ua.Variant(True, ua.VariantType.Boolean))
print("done")