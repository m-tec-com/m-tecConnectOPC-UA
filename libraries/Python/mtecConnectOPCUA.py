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
        self.subscribe("livebit2extern", self.changeLivebit, 500)
    
    """Changes the value of a OPCUA Variable
    Args:
        variable: Variable to change
        value: value to change the variable to
        typ: string of variable type (bool, int, float)
    """
    def change(parameter, value, typ)
        if typ == "bool":
            t = ua.Variant.Boolean
        elif typ == "int":
            t = ua.Variant.UInt16
        elif typ == "float"
            t = ua.Variant.Float
        else:
            return
        self.opcuaClient.get_node(self.baseNode + parameter).set_value(ua.Variant(value, t))

    """Subscribes to given parameter
    Args:
        parameter: the OPC-UA Parameter to subscribe to (check docs for names)
        callback: Callback the variable and timestamp gets passed - callb(value, parameter)
        intervall: Intervall in ms that defined the frequency in which the parameter is checked
    """
    def subscribe(self, parameter, callback, intervall):
        subscriptionHandler = OpcuaSubscriptionHandler(parameter, callback)
        subscription = self.opcuaClient.create_subscription(intervall, subscriptionHandler)
        subscription.subscribe_data_change(self.change("." + nodeName))




    """Changes the Livebit
    Args:
        value: The value to change the Livebit to
    """
    def changeLivebit(self, value, parameter):
        self.change(".Livebit2duoMix", value, "bool")

    """Stops the machine
    """
    def start(self):
        self.change(".Remote_start", True, "bool")

    """Stops the machine
    """
    def stop(self):
        self.change(".Remote_start", False, "bool")

    """Changes the speed of the mixingpump
    Args:
        speed: Speed in Hz
    """
    def setSpeed(self, speed):
        analogSpeed = speed/50*65535 # 50Hz = 65535, 0Hz = 0
        self.change(".set_value_mixingpump", analogSpeed, "int")

    """Changes the state of a Digital Output
    Args:
        pin: Pin number (1 - 8)
        value: true/fale = high/low
    """
    def setDigital(self, pin, value):
        if pin < 1 or pin > 8:
            print("Pin number (" + pin + ") out of range (1 - 8)")
            return 
        self.change(".reserve_DO_" + pin, value, "bool")

    """Changes the state of a Analog Output
    Args:
        pin: Pin number (1 - 2)
        value: value to set 0 to 65535
    """
    def setAnalog(self, pin, value):
        if pin < 1 or pin > 2:
            print("Pin number (" + pin + ") out of range (1 - 2)")
            return 
        self.change(".reserve_AO_" + pin, value, "bool")

    """Reads the speed of the mixingpump
    Returns:
        Speed in Hz
    """
    def getSpeed(self):
        speed = self.change(".actual_value_mixingpump").get_value()
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
        return self.change(".reserve_DI_" + pin).get_value()

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
        return self.change(".reserve_AI_" + pin).get_value()

    """Reads if machine is in error state
    Returns:
        is error? (true/false)
    """
    def isError(self):
        return self.change(".error").get_value()
    
    """Reads the error number of the machine
    Returns:
        error number (0 = none)
    """
    def getError(self):
        return self.change(".error_no").get_value()

    """Checks if the machine is ready for operation (on, remote, mixer and mixingpump on)
    Returns:
        ready for operation (true/false)
    """
    def isReadyForOperation(self):
        return self.change(".Ready_for_operation").get_value()

    """Checks if the mixer is running (in automatic mode)
    Returns:
        mixer running
    """
    def isMixerRunning(self):
        return self.change(".aut_mixer").get_value()

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
        return self.change(".aut_mixingpump_net").get_value()

    """Checks if the mixingpump is running on frequency converter supply (in automatic mode)
    Returns:
        mixingpump is running on frequency converter supply (true/false)
    """
    def isMixingpumpRunningFc(self):
        return self.change(".aut_mixingpump_fc").get_value()

    """Checks if the water pump is running (in automatic mode)
    Returns:
        waterpump is running (true/false)
    """
    def isWaterpump(self):
        return self.change(".aut_waterpump").get_value()

    """Checks if the selenoid valve is open (in automatic mode)
    Returns:
        selenoid valve is open (true/false)
    """
    def isSelenoidValve(self):
        return self.change(".aut_selenoid_valve").get_value()
    
    """Checks if the water pump is running (in automatic mode)
    Returns:
        waterpump is running (true/false)
    """
    def isWaterpump(self):
        return self.change(".aut_waterpump").get_value()

    """Checks if remote is connected
    Returns:
        remote is connected (true/false)
    """
    def isRemote(self):
        return self.change(".Remote_connected").get_value()






class OpcuaSubscriptionHandler:

    def __init__(self, parameter, callback):
        self.parameter = parameter
        self.callback = callback

    def datachange_notification(self, node, value, data):
        self.callback(value, self.parameter)
