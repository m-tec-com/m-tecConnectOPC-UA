from opcua import Client, ua #https://github.com/FreeOpcUa/python-opcua

class Mixingpump:

    def __init__(self, baseNode="ns=4;s=|var|B-Fortis CC-Slim S04.Application.GVL_OPC"):
        self.baseNode = baseNode + "."

    """Connects to the machine using the provided IP
    Args:
        ip: IP-Adress of the machine
    """
    def connect(self, ip):
        self.reader = Client(ip)
        self.writer = Client(ip)
        self.reader.connect()
        self.writer.connect()
        self.reader.load_type_definitions()
        self.writer.load_type_definitions()
        self.subscribe("Livebit2extern", self.changeLivebit, 500)
    
    """Changes the value of a OPCUA Variable
    Args:
        variable: Variable to change
        value: value to change the variable to
        typ: string of variable type (bool, int, float)
    """
    def change(self, parameter, value, typ):
        #print(parameter, value, typ)
        if typ == "bool":
            t = ua.VariantType.Boolean
            value = bool(value)
        elif typ == "int":
            t = ua.VariantType.UInt16
            value = int(value)
        elif typ == "float":
            t = ua.VariantType.Float
            value = float(value)
        else:
            return
        self.writer.get_node(self.baseNode + parameter).set_value(ua.Variant(value, t))

    """Reades the value of a OPCUA Variable
    Args:
        variable: Variable to read
    """
    def read(self, parameter):
        return self.reader.get_node(self.baseNode + parameter).get_value()

    """Subscribes to given parameter
    Args:
        parameter: the OPC-UA Parameter to subscribe to (check docs for names)
        callback: Callback the variable and timestamp gets passed - callb(value, parameter)
        intervall: Intervall in ms that defined the frequency in which the parameter is checked
    """
    def subscribe(self, parameter, callback, intervall):
        subscriptionHandler = OpcuaSubscriptionHandler(parameter, callback)
        subscription = self.reader.create_subscription(intervall, subscriptionHandler)
        handler = subscription.subscribe_data_change(self.reader.get_node(self.baseNode + parameter))
        return [subscription, handler]




    """Changes the Livebit
    Args:
        value: The value to change the Livebit to
    """
    def changeLivebit(self, value, parameter):
        self.change("Livebit2machine", value, "bool")

    """Starts the machine
    """
    def start(self):
        self.change("Remote_start", True, "bool")

    """Stops the machine
    """
    def stop(self):
        self.change("Remote_start", False, "bool")

    """Starts the dosingpump
    """
    def startDosingpump(self):
        self.change("state_dosingpump_on", True, "bool")

    """Stops the dosingpump
    """
    def stopDosingpump(self):
        self.change("state_dosingpump_on", False, "bool")

    """Changes the speed of the dosingpump
    Args:
        speed: Speed in %
    """
    def setSpeedDosingpump(self, speed):
        self.change("set_value_dosingpump", int(speed), "float")

    """Changes the speed of the mixingpump
    Args:
        speed: Speed in Hz
    """
    def setSpeed(self, speed):
        analogSpeed = speed/100*65535 # 100% = 65535, 0% = 0
        self.change("set_value_mixingpump", int(analogSpeed), "int")

    """Changes the water setting of the mixingpump
    Args:
        speed: amount in l/h
    """
    def setWater(self, speed):
        self.change("set_value_water_flow", float(speed), "float")

    """Changes the state of a Digital Output
    Args:
        pin: Pin number (1 - 8)
        value: true/fale = high/low
    """
    def setDigital(self, pin, value):
        if pin < 1 or pin > 8:
            print("Pin number (" + str(pin) + ") out of range (1 - 8)")
            return 
        self.change("reserve_DO_" + str(pin), value, "bool")

    """Changes the state of a Analog Output
    Args:
        pin: Pin number (1 - 2)
        value: value to set 0 to 65535
    """
    def setAnalog(self, pin, value):
        if pin < 1 or pin > 2:
            print("Pin number (" + str(pin) + ") out of range (1 - 2)")
            return 
        self.change("reserve_AO_" + str(pin), value, "int")

    """Reads the speed of the mixingpump
    Returns:
        Speed in Hz
    """
    def getSpeed(self):
        speed = self.read("actual_value_mixingpump")
        return speed/65535*50 # 50Hz = 65535, 0Hz = 0
    
    """Reads the set amount of water
    Returns:
        Amount in l/H
    """
    def getSetWater(self):
        return self.read("set_value_water_flow")

    """Reads the state of a Digital Input
    Args:
        pin: Pin number (1 - 10)
    Returns:
        actual value (true / false)
    """
    def getDigital(self, pin):
        if pin < 1 or pin > 10:
            print("Pin number (" + str(pin) + ") out of range (1 - 10)")
            return
        return self.read("reserve_DI_" + str(pin))

    """Reads the state of a Analog Input
    Args:
        pin: Pin number (1 - 5)
    Returns:
        actual value (0 - 65535)
    """
    def getAnalog(self, pin):
        if pin < 1 or pin > 5:
            print("Pin number (" + str(pin) + ") out of range (1 - 5)")
            return
        return self.read("reserve_AI_" + str(pin))

    """Reads if machine is in error state
    Returns:
        is error? (true/false)
    """
    def isError(self):
        return self.read("error")
    
    """Reads the error number of the machine
    Returns:
        error number (0 = none)
    """
    def getError(self):
        return self.read("error_no")

    """Checks if the machine is ready for operation (on, remote, mixer and mixingpump on)
    Returns:
        ready for operation (true/false)
    """
    def isReadyForOperation(self):
        return self.read("Ready_for_operation")

    """Checks if the mixer is running (in automatic mode)
    Returns:
        mixer running
    """
    def isMixerRunning(self):
        return self.read("aut_mixer")

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
        return self.read("aut_mixingpump_net")

    """Checks if the mixingpump is running on frequency converter supply (in automatic mode)
    Returns:
        mixingpump is running on frequency converter supply (true/false)
    """
    def isMixingpumpRunningFc(self):
        return self.read("aut_mixingpump_fc")

    """Checks if the selenoid valve is open (in automatic mode)
    Returns:
        selenoid valve is open (true/false)
    """
    def isSolenoidValve(self):
        return self.read("aut_solenoid_valve")
    
    """Checks if the water pump is running (in automatic mode)
    Returns:
        waterpump is running (true/false)
    """
    def isWaterpump(self):
        return self.read("aut_waterpump")

    """Checks if remote is connected
    Returns:
        remote is connected (true/false)
    """
    def isRemote(self):
        return self.read("Remote_connected")






class OpcuaSubscriptionHandler:

    def __init__(self, parameter, callback):
        self.parameter = parameter
        self.callback = callback

    def datachange_notification(self, node, value, data):
        self.callback(value, self.parameter)
