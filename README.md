\# Keithley 6485 Control



Python SCPI control and buffered data acquisition tool for the  

Keithley 6485 Picoammeter.



---



\## Overview



This project provides a minimal and clean Python interface for controlling a  

Keithley 6485 Picoammeter via serial communication.



It implements:



\- Serial SCPI communication

\- High-speed buffered measurements

\- Automatic NumPy-based data parsing

\- Optional Matplotlib data visualization



The fast measurement routine follows Programming Example C-2  

from the Keithley 6485 / 6487 User Manual.



---



\## Features



\- Serial connect / disconnect

\- Device identification via `\*IDN?`

\- Device reset via `\*RST`

\- Fast buffered acquisition using `TRAC:DATA?`

\- Configurable trigger count and integration time

\- NumPy-based data parsing

\- Optional plotting functionality



---



\## Requirements



\- Python 3.10+

\- pyserial

\- numpy

\- matplotlib

\- pyfiglet

\- colorama



Install dependencies:



```bash

pip install -r requirements.txt

