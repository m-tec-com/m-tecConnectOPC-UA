from opcua import Client, ua      

# connect
reader = Client("opc.tcp://10.129.4.73:4840")
reader.connect()
reader.load_type_definitions()

# subscription
class SubscriptionHandler(object):
    def datachange_notification(self, node, value, data):
        print("Subscription-Temperature:", value/10000*100)

node = reader.get_node("ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC.reserve_AI_2")
subHandler = SubscriptionHandler()
sub = reader.create_subscription(100, subHandler)
subscription = sub.subscribe_data_change(node)