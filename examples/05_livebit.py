from opcua import Client, ua      

# connect
reader = Client("opc.tcp://10.129.4.73:4840")
reader.connect()
reader.load_type_definitions()

# connect
writer = Client("opc.tcp://10.129.4.73:4840")
writer.connect()
writer.load_type_definitions()

# toggle Livebit by subscription
class LivebitHandler(object):
    def datachange_notification(self, node, value, data):
        print("Livebit:", value)
        
        # use the OPC-UA variable Livebit2DuoMix when using a duo-mix, Livebit2machine when using a SMP
        Livebit2machine = writer.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.Livebit2DuoMix")
        #Livebit2machine = writer.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.Livebit2machine")
        
        Livebit2machine.set_value(ua.Variant(value, ua.VariantType.Boolean))

Livebit2extern = reader.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.Livebit2extern")
subHandler = LivebitHandler()
sub = reader.create_subscription(100, subHandler)
subscription = sub.subscribe_data_change(Livebit2extern)
