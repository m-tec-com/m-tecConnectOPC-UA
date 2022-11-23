# m-tecConnectOPC-UA

## Supported Machines

The duo-mix connect and SMP connect use OPC UA as communication protocol. ([The P20 connect and P50 connect use Modbus RTU instead.](https://github.com/m-tec-com/m-tecConnectModbus))

## Connection

Connect the machine with the control unit (or your PC) with an ethernet cable.

You might have to change the IP-Range of your control unit (or PC).

The IP-Adress of the OPC UA server in the duo-mix connect and SMP connect is `10.129.4.73`.

## Communication

To get started you can use [uaExpert from Unified Automation](https://www.unified-automation.com/products/development-tools/uaexpert.html).

When controlling the machine externally you have to send a toggle-bit.
Simply subscribe to `Livebit2extern` and actively update `Livebit2DuoMix` at the duo-mix connect. Check out the [example](examples/05_livebit.py)

> :warning:
>
> Use `Livebit2machine` instead of `Livebit2DuoMix` at the SMP connect.
