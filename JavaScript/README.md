> :warning: &nbsp; This library has been updated to match the Python implementation. It now includes both the base `ModbusMachine` class and the `Pump` class for better structure and functionality.

&nbsp;

# Usage

## Minimal init

```html
<script src="https://cdn.jsdelivr.net/gh/m-tec-com/mtecconnect3dcp/JavaScript/mtecconnect3dcp.js"></script>
<script>
    // Using the legacy class (backward compatible)
    var pump = new mtecConnectModbus();
    
    // Or using the new structure
    var pump = new Pump();

    async function connect() {
        var connected = await pump.connect();
        if (!connected) {
            console.log("Connection failed");
            return;
        }
     }
    
    async function start(){
        await pump.setSpeed(20);
    }
    
    async function stop(){
        await pump.setSpeed(0);
    }
</script>
<button onclick="connect()">Connect</button>
<button onclick="start()">Start</button>
<button onclick="stop()">Stop</button>
```
> :warning: &nbsp; Keep in mind:
> * `.connect()` has to be triggered by user gesture (e.g. onclick)
> * communication takes some time &rarr; use async functions and await

&nbsp;

## New API Structure

The library now provides two main classes:

### ModbusMachine (Base Class)
Provides low-level Modbus communication methods:
- `connect()` - Connect to serial port
- `disconnect()` - Disconnect from serial port  
- `read(command)` - Read from Modbus device
- `write(command, value)` - Write to Modbus device
- `keepalive(callback, interval)` - Start keepalive loop
- `stopKeepalive()` - Stop keepalive loop

### Pump (Extends ModbusMachine)
Provides pump-specific functionality with both new methods and backward-compatible properties.

&nbsp;

## Documentation

### :wrench: &nbsp; :boom: &nbsp; constructor

Creates the Object to use the library.

```javascript
// Legacy constructor (backward compatible)
var pump = new mtecConnectModbus(inverterNumber);

// New constructors
var pump = new Pump(inverterNumber, baudRate, log);
var machine = new ModbusMachine(inverterNumber, baudRate, log);
```

parameters:
* string (length: 2), inverter number (parameter F802), optional (default: "01")
* number, serial baudrate, optional (default: 19200)
* boolean, enable logging, optional (default: false)

result:
* mtecConnectModbus/Pump/ModbusMachine, contains everything used to communicate via modbus

&nbsp;

### :wrench: &nbsp; :electric_plug: &nbsp; connect

Connects to the serial converter.

> :memo: &nbsp; `.connect()` has to be triggered by user gesture (e.g. onclick)

```javascript
var connected = await pump.connect(); // has to be triggered by user gesture (e.g. onclick)
```

result:
* bool, connection to serial interface successful?

&nbsp;

### :wrench: &nbsp; :electric_plug: &nbsp; disconnect

Disconnects from the serial converter.

```javascript
await pump.disconnect();
```

&nbsp;

### :gear: &nbsp; :arrows_counterclockwise: &nbsp; keep alive

> :memo: &nbsp; While the pump is running, a valid command has to be sent at least every second

```javascript
// New method
pump.keepalive(callback, interval);  // Start keepalive
pump.stopKeepalive();               // Stop keepalive

// Legacy method (still supported)
pump.settings.keepAlive.active = true;
pump.keepAlive();
```

The legacy settings structure is still supported:
* bool `pump.settings.keepAlive.active`, if keep alive feature is enabled, default: false
* int `pump.settings.keepAlive.interval`, interval after which the command is sent (in ms), default: 250
* string `pump.settings.keepAlive.command`, default: "03FD000001"
* function `pump.settings.keepAlive.callback`, gets called with return value as parameter, optional

&nbsp;

### :wrench: &nbsp; :arrow_forward: &nbsp; start & stop

Starts or stops the pump (target frequency has to be set)

```javascript
// New properties (recommended)
await (pump.run = true);     // Start the pump
await (pump.run = false);    // Stop the pump
await (pump.reverse = true); // Set reverse direction
await (pump.reverse = false);// Set forward direction

// Legacy methods (still supported)
await pump.start();         // starts the pump
await pump.startReverse();  // starts the pump in reverse
await pump.stop();          // stops the pump
```

&nbsp;

### :pencil2: &nbsp; :timer_clock: &nbsp; set frequency

Sets the target frequency

```javascript
// Property syntax (recommended)
await (pump.frequency = frequency);

// Legacy syntax (also supported)
await (pump._frequency = frequency);
```

parameters:
* float, positive (resolution: 0.01), target frequency in Hz

&nbsp;

### :mag: &nbsp; :timer_clock: &nbsp; get frequency

Gets the actual frequency

```javascript
// Property syntax (recommended)
var frequency = await pump.frequency;

// Legacy syntax (also supported)  
var frequency = await pump._frequency;
```

result:
* float, positive (resolution: 0.01), actual frequency in Hz

&nbsp;

### :pencil2: &nbsp; :fast_forward: &nbsp; set speed

Starts (or stops) the pump in the desired direction

> :warning: &nbsp; Do not switch between `set frequency` and `set speed`

```javascript
// Property syntax (recommended)
await (pump.speed = speed);
```

parameters:
* float, negative to reverse (resolution: 0.01), target frequency

&nbsp;

### :mag: &nbsp; :vertical_traffic_light: &nbsp; get ready

Gets the readiness of the machine (on)

```javascript
// Property syntax (recommended)
var ready = await pump.s_ready;

// Legacy property (also supported)
var ready = await pump.ready;
```

result:
* bool, machine is ready for operation

&nbsp;

### :mag: &nbsp; :zap: &nbsp; get voltage

Gets the actual output voltage

```javascript
// Property syntax (recommended)
var voltage = await pump.m_voltage;

// Legacy property (also supported)
var voltage = await pump.voltage;
```

result:
* float, positive (resolution: 0.01), actual voltage in % of voltage rating

&nbsp;

### :mag: &nbsp; :bulb: &nbsp; get current

Gets the actual output current

```javascript
// Property syntax (recommended)
var current = await pump.m_current;

// Legacy property (also supported)
var current = await pump.current;
```

result:
* float, positive (resolution: 0.01), actual current in % of current rating

&nbsp;

### :mag: &nbsp; :muscle: &nbsp; get torque

Gets the actual torque

```javascript
// Property syntax (recommended)
var torque = await pump.m_torque;

// Legacy property (also supported)
var torque = await pump.torque;
```

result:
* float, positive (resolution: 0.01), actual torque in % of torque rating

&nbsp;

### :mag: &nbsp; Additional Status Properties

New status properties available in the Pump class:

```javascript
var pumping = await pump.s_pumping;         // Is pump running?
var forward = await pump.s_pumping_forward; // Is pump running forward?
var reverse = await pump.s_pumping_reverse; // Is pump running in reverse?
var running = await pump.run;               // Is pump set to run?
var isReverse = await pump.reverse;         // Is reverse direction set?
var realSpeed = await pump.m_speed;         // Real speed (negative if reverse)
var setSpeed = pump.speed;                  // Get set speed (synchronous)
```

&nbsp;

### :wrench: &nbsp; :hash: &nbsp; send custom command

Sends custom command to inverter

```javascript
// New methods (recommended)
var answer = await pump.read(parameter);        // Read command
var answer = await pump.write(parameter, value); // Write command

// Legacy method (still supported)
var answer = await pump.sendCommand(parameter, value);
```

parameters:
* string (length: 4-6), parameter number for read, or action + parameter for legacy method
* int, value (for write commands)

result:
* int, answer value (equals input value if write command)

&nbsp;

## Migration Guide

The library now uses getter/setter properties like the Python implementation:

```javascript
// Property-based API (recommended - matches Python structure)
await (pump.run = true);
await (pump.reverse = false);
await (pump.frequency = 50);
var speed = await pump.m_speed;
var voltage = await pump.m_voltage;

// Legacy property syntax (still supported)
await (pump.speed = 50);
var freq = await pump.frequency;
```

The property names now match the Python implementation:
- `s_ready` - machine ready status
- `run` - pump running state
- `reverse` - reverse direction state  
- `s_pumping` - pump is running
- `s_pumping_forward` - pump running forward
- `s_pumping_reverse` - pump running reverse
- `_frequency` - internal frequency control
- `m_voltage`, `m_current`, `m_torque` - measured values
- `m_speed` - measured speed
- `speed` - set speed (getter only returns last set value)