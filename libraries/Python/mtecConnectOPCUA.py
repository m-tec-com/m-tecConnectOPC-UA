# ToDo: LiveBit

from opcua import Client, ua #https://github.com/FreeOpcUa/python-opcua

class Mixingpump:

    def __init__(self):
        self.baseNode = "ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC"

    """Connects to the machine using the provided IP
    Args:
        ip: IP-Adress of the machine
    """
    def connect(self, ip):
        self.opcuaClient = Client(ip)
        self.opcuaClient.connect()
        self.opcuaClient.load_type_definitions()
        
    """Stops the machine
    """
    def start(self):
        self.opcuaClient.get_node(self.baseNode + ".Remote_start").set_value(ua.Variant(True, ua.VariantType.Boolean))

    """Stops the machine
    """
    def stop(self):
        self.opcuaClient.get_node(self.baseNode + ".Remote_start").set_value(ua.Variant(False, ua.VariantType.Boolean))

    """Changes the speed of the mixingpump
    Args:
        speed: Speed in Hz
    """
    def setSpeed(self, speed):
        analogSpeed = speed/50*65535 # 50Hz = 65535, 0Hz = 0
        self.opcuaClient.get_node(self.baseNode + ".set_value_mixingpump").set_value(ua.Variant(analogSpeed, ua.VariantType.UInt16))

    """Changes the state of a Digital Output
    Args:
        pin: Pin number (1 - 8)
        value: true/fale = high/low
    """
    def setDigital(self, pin, value):
        if pin < 1 or pin > 8:
            print("Pin number (" + pin + ") out of range (1 - 8)")
            return 
        self.opcuaClient.get_node(self.baseNode + ".reserve_DO_" + pin).set_value(ua.Variant(value, ua.VariantType.Boolean))

    """Changes the state of a Analog Output
    Args:
        pin: Pin number (1 - 2)
        value: value to set 0 to 65535
    """
    def setAnalog(self, pin, value):
        if pin < 1 or pin > 2:
            print("Pin number (" + pin + ") out of range (1 - 2)")
            return 
        self.opcuaClient.get_node(self.baseNode + ".reserve_AO_" + pin).set_value(ua.Variant(value, ua.VariantType.Boolean))

    """Reads the speed of the mixingpump
    Returns:
        Speed in Hz
    """
    def getSpeed(self):
        speed = self.opcuaClient.get_node(self.baseNode + ".actual_value_mixingpump").get_value()
        return speed/65535*50 # 50Hz = 65535, 0Hz = 0

    """Reads the state of a Digital Input
    Args:
        pin: Pin number (1 - 10)
    Returns:
        actual value (true / false)
    """
    def getDigital(self, pin, value):
        if pin < 1 or pin > 10:
            print("Pin number (" + pin + ") out of range (1 - 10)")
            return
        return self.opcuaClient.get_node(self.baseNode + ".reserve_DI_" + pin).get_value()

    """Reads the state of a Analog Input
    Args:
        pin: Pin number (1 - 5)
    Returns:
        actual value (0 - 65535)
    """
    def getAnalog(self, pin, value):
        if pin < 1 or pin > 5:
            print("Pin number (" + pin + ") out of range (1 - 5)")
            return
        return self.opcuaClient.get_node(self.baseNode + ".reserve_AI_" + pin).get_value()

    """Reads if machine is in error state
    Returns:
        is error? (true/false)
    """
    def isError(self):
        return self.opcuaClient.get_node(self.baseNode + ".error").get_value()
    
    """Reads the error number of the machine
    Returns:
        error number (0 = none)
    """
    def getError(self):
        return self.opcuaClient.get_node(self.baseNode + ".error_no").get_value()

    """Checks if the machine is ready for operation (on, remote, mixer and mixingpump on)
    Returns:
        ready for operation (true/false)
    """
    def isReadyForOperation(self):
        return self.opcuaClient.get_node(self.baseNode + ".Ready_for_operation").get_value()

    """Checks if the mixer is running (in automatic mode)
    Returns:
        mixer running
    """
    def isMixerRunning(self):
        return self.opcuaClient.get_node(self.baseNode + ".aut_mixer").get_value()

    """Checks if the mixingpump is running
    Returns:
        mixingpump is running (true/false)
    """
    def isMixingpumpRunning(self):
        return self.isMixingpumpRunningNet() or self.isMixingpumpRunningFc()

    """Checks if the mixingpump is running on power supply (in automatic mode)
    Returns:
        mixingpump is running on power supply (true/false)
    """
    def isMixingpumpRunningNet(self):
        return self.opcuaClient.get_node(self.baseNode + ".aut_mixingpump_net").get_value()

    """Checks if the mixingpump is running on frequency converter supply (in automatic mode)
    Returns:
        mixingpump is running on frequency converter supply (true/false)
    """
    def isMixingpumpRunningFc(self):
        return self.opcuaClient.get_node(self.baseNode + ".aut_mixingpump_fc").get_value()

    """Checks if the water pump is running (in automatic mode)
    Returns:
        waterpump is running (true/false)
    """
    def isWaterpump(self):
        return self.opcuaClient.get_node(self.baseNode + ".aut_waterpump").get_value()

    """Checks if the selenoid valve is open (in automatic mode)
    Returns:
        selenoid valve is open (true/false)
    """
    def isSelenoidValve(self):
        return self.opcuaClient.get_node(self.baseNode + ".aut_selenoid_valve").get_value()
    
    """Checks if the water pump is running (in automatic mode)
    Returns:
        waterpump is running (true/false)
    """
    def isWaterpump(self):
        return self.opcuaClient.get_node(self.baseNode + ".aut_waterpump").get_value()

    """Checks if remote is connected
    Returns:
        remote is connected (true/false)
    """
    def isRemote(self):
        return self.opcuaClient.get_node(self.baseNode + ".Remote_connected").get_value()

    """Subscribes to given parameter
    Args:
        parameter: Parameter to subscribe to (same as is[...] or get[...])
        callback: Callback the variable and timestamp gets passed - callb(value, parameter)
        intervall: Intervall in ms that defined the frequency in which the parameter is checked
    """
    def subscribe(self, parameter, callback, intervall):
        nodeName = "" #ToDo get nodeName
        subscriptionHandler = OpcuaSubscriptionHandler(parameter, callback)
        subscription = self.opcuaClient.create_subscription(intervall, subscriptionHandler)
        subscription.subscribe_data_change(self.opcuaClient.get_node(self.baseNode + "." + nodeName))

class OpcuaSubscriptionHandler:

    def __init__(self, parameter, callback):
        self.parameter = parameter
        self.callback = callback

    def datachange_notification(self, node, value, data):
        self.callback(value, self.parameter)
