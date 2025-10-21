/**
 * Base class for Modbus machine communication via Web Serial API.
 * Provides low-level communication methods for Modbus RTU protocol.
 */
class ModbusMachine {
    /**
     * Creates a new ModbusMachine instance.
     * @param {string} frequencyInverterID - ID of the frequency inverter (default '01')
     * @param {number} baudRate - Serial baudrate (default 19200)
     * @param {boolean} log - Enable logging (default false)
     */
    constructor(frequencyInverterID = "01", baudRate = 19200, log = false) {
        this._frequencyInverterID = frequencyInverterID;
        this._baudRate = baudRate;
        this._logging = log;
        this._connected = false;
        this._port = null;
        this._reader = null;
        this._keepaliveTimer = null;
        this._keepaliveInterval = 250; // milliseconds
        this._timeout = 200; // milliseconds
        this._keepaliveCommand = "03FD000001";
        this._keepaliveCallback = null;
        
        this.temp = {
            "sendBuffer": [],
            "valueBuffer": [],
            "readBuffer": [],
            "sendReady": false
        };
        
        this.settings = {
            "serial": {
                baudRate: baudRate,
                dataBits: 8,
                stopBits: 2,
                parity: "none",
                flowControl: "none"
            },
            "log": log,
            "sendCallback": undefined,
            "receivedCallback": undefined
        };
        
        this.available = ("serial" in navigator);
    }

    /**
     * Connects to the Modbus machine using Web Serial API.
     * @returns {Promise<boolean>} True if connection successful
     */
    async connect() {
        try {
            this._port = await navigator.serial.requestPort();
            await this._port.open(this.settings.serial);
            this._connected = true;
            this._reader = this._port.readable.getReader();
            this.temp.sendReady = true;
            this._log("Connected to serial port");
            this._readLoop();
            return true;
        } catch (error) {
            this._log(`Connection failed: ${error.message}`);
            return false;
        }
    }

    /**
     * Disconnects from the Modbus machine.
     */
    async disconnect() {
        if (this._reader) {
            await this._reader.cancel();
            await this._reader.releaseLock();
            this._reader = null;
        }
        if (this._port && this._port.readable) {
            await this._port.close();
        }
        this._connected = false;
        this.stopKeepalive();
        this._log("Disconnected");
    }

    /**
     * Reads a value from the Modbus machine.
     * @param {string} command - The Modbus command to read
     * @returns {Promise<any>} The value read from the machine
     */
    async read(command) {
        return await this._sendCommand("03" + command, 1);
    }

    /**
     * Writes a value to the Modbus machine.
     * @param {string} command - The Modbus command to write
     * @param {number} value - The value to write
     * @returns {Promise<any>} The response from the machine
     */
    async write(command, value) {
        return await this._sendCommand("06" + command, value);
    }

    async _readLoop() {
        try {
            while (this._connected) {
                const { value, done } = await this._reader.read();
                if (done) break;
                if (value) {
                    this._log(`Read: ${Array.from(value).map(b => b.toString(16).padStart(2, '0')).join(' ')}`);
                    this._received(value);
                }
            }
        } catch (error) {
            this._log(`Read loop error: ${error.message}`);
        }
    }

    async _sendCommand(parameter, value) {
        const data = this._frequencyInverterID + parameter + this._int2hex(value, 4);
        return await this._sendHexCommand(data);
    }

    async _sendHexCommand(data) {
        const crc = this._calcCRC(data);
        const command = data + crc;
        return await this._sendAndReceive(command);
    }

    async _sendAndReceive(command) {
        if (!this._connected || !this._port) {
            throw new Error("Not connected to Modbus machine.");
        }
        
        this.temp.sendBuffer.push(command);
        this._sendHex();
        await this._until(() => this.temp.valueBuffer.length > 0);
        const response = this.temp.valueBuffer.shift();
        this._log(`Response: ${JSON.stringify(response)}`);
        return response ? response.value : null;
    }

    /**
     * Starts a keepalive loop sending a command at a regular interval.
     * @param {Function} callback - Function to call with the response
     * @param {number} interval - Interval in milliseconds
     */
    keepalive(callback = null, interval = 250) {
        this._keepaliveCallback = callback;
        this._keepaliveInterval = interval;
        this._keepaliveLoop();
    }

    async _keepaliveLoop() {
        if (!this._connected) return;
        
        try {
            const value = await this._sendHexCommand(this._frequencyInverterID + this._keepaliveCommand);
            if (this._keepaliveCallback && typeof this._keepaliveCallback === 'function') {
                this._keepaliveCallback(value);
            }
        } catch (error) {
            this._log(`Keepalive error: ${error.message}`);
        }
        
        this._keepaliveTimer = setTimeout(() => this._keepaliveLoop(), this._keepaliveInterval);
    }

    /**
     * Stops the keepalive loop.
     */
    stopKeepalive() {
        if (this._keepaliveTimer) {
            clearTimeout(this._keepaliveTimer);
            this._keepaliveTimer = null;
        }
    }

    _sendHex() {
        if (this.temp.sendReady && this.temp.sendBuffer.length > 0) {
            this._send(this.temp.sendBuffer.shift());
        }
    }

    _send(hex) {
        if (typeof this.settings.sendCallback === "function") {
            this.settings.sendCallback(hex);
        }

        this.temp.sendReady = false;
        const hexArray = this._hex2array(hex);
        const writer = this._port.writable.getWriter();
        writer.write(hexArray);
        writer.releaseLock();
        this._log(`Sent: ${hex}`);
    }

    _received(inputValues) {
        for (const value of inputValues) {
            this.temp.readBuffer.push(value);
        }
        const values = this.temp.readBuffer;

        let completeDataLength = Infinity;
        if (this.temp.readBuffer.length >= 3) {
            if (this.temp.readBuffer[1] === 3) {
                // Type: read
                const dataLength = this.temp.readBuffer[2];
                completeDataLength = 3 + dataLength + 2;
                // ID, Type, Length, <Length>, checksum, checksum
            } else if (this.temp.readBuffer[1] === 6) {
                // Type: write single Block
                completeDataLength = 8;
            }
        }

        if (this.temp.readBuffer.length >= completeDataLength) {
            this._log(`Received: ${this.temp.readBuffer.slice(0, completeDataLength)}`);
            this.temp.readBuffer = this.temp.readBuffer.slice(completeDataLength);

            const message = {};
            message.fcID = values[0];
            message.type = values[1];
            
            if (message.type === 6) {
                message.param = this._int2hex(values[2] * 256 + values[3], 4);
                message.value = values[4] * 256 + values[5];
                message.crc = this._int2hex(values[6] * 256 + values[7], 4);
            } else if (message.type === 3) {
                message.length = this._int2hex(values[2], 2);
                const dataLength = values[2];
                message.value = 0;
                for (let i = 0; i < dataLength; i++) {
                    message.value *= 256;
                    message.value += values[i + 3];
                }
                message.crc = this._int2hex(values[3 + dataLength] * 256 + values[4 + dataLength], 4);
            }
            
            let command = "";
            for (let i = 0; i < completeDataLength - 2; i++) {
                command += this._int2hex(values[i], 2);
            }
            
            if (this._calcCRC(command) !== message.crc) {
                this._log("CRC error");
                return;
            }
            
            this.temp.valueBuffer.push(message);

            if (typeof this.settings.receivedCallback === "function") {
                this.settings.receivedCallback(command + message.crc);
            }

            this.temp.sendReady = true;
            this._sendHex();
        }
    }

    _until(conditionFunction) {
        const poll = resolve => {
            if (conditionFunction())
                resolve();
            else
                setTimeout(() => poll(resolve), 10);
        };
        return new Promise(poll);
    }

    _calcCRC(command) {
        const buffer = this._hex2array(command);
        let crc = 0xFFFF;
        for (let pos = 0; pos < buffer.length; pos++) {
            crc ^= buffer[pos];
            for (let i = 8; i !== 0; i--) {
                if ((crc & 0x0001) !== 0) {
                    crc >>= 1;
                    crc ^= 0xA001;
                } else {
                    crc >>= 1;
                }
            }
        }
        const reversed = (crc % 256) * 256 + Math.floor(crc / 256);
        return this._int2hex(reversed, 4);
    }

    _int2hex(value, length) {
        let s = Math.round(value).toString(16).toUpperCase();
        while (s.length < length) {
            s = "0" + s;
        }
        return s;
    }
    
    _hex2int(hex) {
        return parseInt(hex, 16);
    }
    
    _hex2array(hexString) {
        return new Uint8Array(hexString.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
    }

    _log(content) {
        if (this._logging) {
            console.log(`[ModbusMachine] ${content}`);
        }
    }

    // Getter for connection status
    get connected() {
        return this._connected;
    }
}


/**
 * Class for controlling a pump via Modbus.
 * Inherits from ModbusMachine.
 */
class Pump extends ModbusMachine {
    // Class-level bit masks for status decoding
    static _RUNNING_MASK = 0x0400;
    static _REVERSE_MASK = 0x0200;

    constructor(...args) {
        super(...args);
        this._lastSpeed = 0.0;
        this._lastRunning = false;
        this._lastReverse = false;
    }

    /**
     * True if the machine is ready for operation (on, remote, mixer and mixingpump on).
     * @returns {Promise<boolean>}
     */
    get s_ready() {
        return (async () => {
            const switches = await this.read("FD06");
            return ((switches % 32) - (switches % 16) !== 0);
        })();
    }

    /**
     * True if the pump is set to run, False otherwise.
     * @returns {Promise<boolean>}
     */
    get run() {
        return (async () => {
            const value = await this.read("FA00");
            return (value & Pump._RUNNING_MASK) !== 0;
        })();
    }

    /**
     * Set the running state of the pump.
     * @param {boolean} state - True to start, False to stop
     */
    set run(state) {
        return (async () => {
            let result;
            if (state) {
                if (this._lastReverse) {
                    result = await this.write("FA00", 0xC600);
                } else {
                    result = await this.write("FA00", 0xC400);
                }
                if(!this._lastRunning){
                    this.keepalive();
                }
            } else {
                result = await this.write("FA00", 0x0000);
                if(this._lastRunning){
                    this.stopKeepalive();
                }
            }
            this._lastRunning = state;
            return result;
        })();
    }

    /**
     * True if the pump is running, False otherwise.
     * @returns {Promise<boolean>}
     */
    get s_pumping() {
        return (async () => {
            const speed = await this.m_speed;
            return Math.abs(speed) > 0;
        })();
    }

    /**
     * True if the pump is running forward, False otherwise.
     * @returns {Promise<boolean>}
     */
    get s_pumping_forward() {
        return (async () => {
            const speed = await this.m_speed;
            return speed > 0;
        })();
    }

    /**
     * True if the pump is running in reverse, False otherwise.
     * @returns {Promise<boolean>}
     */
    get s_pumping_reverse() {
        return (async () => {
            const speed = await this.m_speed;
            return speed < 0;
        })();
    }

    /**
     * True if the pump is running in reverse, False otherwise.
     * @returns {Promise<boolean>}
     */
    get reverse() {
        return (async () => {
            const value = await this.read("FA00");
            return (value & Pump._REVERSE_MASK) !== 0;
        })();
    }

    /**
     * Set the running direction of the pump.
     * @param {boolean} state - True for reverse, False for forward
     */
    set reverse(state) {
        return (async () => {
            this._lastReverse = state;
            if (this._lastRunning) {
                if (state) {
                    return await this.write("FA00", 0xC600);
                } else {
                    return await this.write("FA00", 0xC400);
                }
            } else {
                return await this.write("FA00", 0x0000);
            }
        })();
    }

    /**
     * Frequency of the pump in Hz.
     * @returns {Promise<number>}
     */
    get _frequency() {
        return (async () => {
            return (await this.read("FD00")) / 100;
        })();
    }

    /**
     * Set the frequency of the pump.
     * @param {number} value - Frequency in Hz
     */
    set _frequency(value) {
        return (async () => {
            return await this.write("FA01", Math.round(value * 100));
        })();
    }

    /**
     * Voltage of the pump in V.
     * @returns {Promise<number>}
     */
    get m_voltage() {
        return (async () => {
            return (await this.read("FD05")) / 100;
        })();
    }

    /**
     * Current of the pump in A.
     * @returns {Promise<number>}
     */
    get m_current() {
        return (async () => {
            return (await this.read("FD03")) / 100;
        })();
    }

    /**
     * Torque of the pump in Nm.
     * @returns {Promise<number>}
     */
    get m_torque() {
        return (async () => {
            return (await this.read("FD18")) / 100;
        })();
    }

    /**
     * Emergency stop for the pump.
     * @returns {Promise<any>}
     */
    async emergencyStop() {
        return await this.write("FA00", 0x1000);
    }

    /**
     * Real speed of the pump in Hz. Negative values indicate reverse direction.
     * @returns {Promise<number>}
     */
    get m_speed() {
        return (async () => {
            const frequency = await this._frequency;
            const isReverse = await this.reverse;
            return isReverse ? -frequency : frequency;
        })();
    }

    /**
     * Get the set speed of the pump.
     * @returns {number}
     */
    get speed() {
        return this._lastSpeed;
    }

    /**
     * Set the speed of the pump.
     * @param {number} value - Speed. Negative values indicate reverse direction.
     */
    set speed(value) {
        return (async () => {
            if (value === this._lastSpeed) {
                return;
            }
            if (value === 0) {
                await (this.run = false);
            } else {
                if (value < 0 && !(this._lastSpeed < 0)) {
                    await (this.reverse = true);
                } else if (value > 0 && !(this._lastSpeed > 0)) {
                    await (this.reverse = false);
                }
                await (this._frequency = Math.abs(value));
            }
            this._lastSpeed = value;
        })();
    }

    // Backward compatibility methods
    async start() {
        /**
         * DEPRECATED: Use 'run = true' instead.
         */
        await (this.reverse = false);
        await (this.run = true);
    }

    async startReverse() {
        /**
         * DEPRECATED: Use 'reverse = true' and 'run = true' instead.
         */
        await (this.reverse = true);
        await (this.run = true);
    }

    async stop() {
        /**
         * DEPRECATED: Use 'run = false' instead.
         */
        await (this.run = false);
    }

    // Legacy property-style accessors for backward compatibility
    get ready() {
        return this.s_ready;
    }

    get frequency() {
        return this._frequency;
    }

    set frequency(value) {
        return this._frequency = value;
    }

    get voltage() {
        return this.m_voltage;
    }

    get current() {
        return this.m_current;
    }

    get torque() {
        return this.m_torque;
    }
}

// Backward compatibility - alias for the old class name
class mtecConnectModbus extends Pump {
    constructor(frequencyInverterID = "01") {
        super(frequencyInverterID);
        // Legacy settings structure for backward compatibility
        this.settings = {
            "frequencyInverterID": frequencyInverterID,
            "keepAlive": {
                "command": "03FD000001",
                "interval": 250,
                "callback": undefined,
                "active": false
            },
            "serial": {
                baudRate: 19200,
                dataBits: 8,
                stopBits: 2,
                parity: "none",
                flowControl: "none"
            },
            "log": false,
            "sendCallback": undefined,
            "receivedCallback": undefined
        };
        
        // Sync settings with parent
        this._logging = this.settings.log;
        this._keepaliveCommand = this.settings.keepAlive.command;
        this._keepaliveInterval = this.settings.keepAlive.interval;
        this._keepaliveCallback = this.settings.keepAlive.callback;
        
        // Legacy temp structure
        this.temp = {
            "sendBuffer": this.temp.sendBuffer,
            "valueBuffer": this.temp.valueBuffer,
            "readBuffer": this.temp.readBuffer,
            "sendReady": this.temp.sendReady,
            "lastSpeed": 0
        };
    }

    // Override keepAlive to maintain backward compatibility
    async keepAlive() {
        if (this.settings.keepAlive.active) {
            this.keepalive(this.settings.keepAlive.callback, this.settings.keepAlive.interval);
        } else {
            this.stopKeepalive();
        }
    }
}