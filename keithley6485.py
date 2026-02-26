import time
import serial
from pyfiglet import figlet_format
from colorama import init
import os
import platform
import matplotlib.pyplot as plt
import numpy as np




class Keithley6485:
    """
    @brief Treiberklasse zur seriellen Ansteuerung eines Keithley 6485 Picoammeters.

    Diese Klasse implementiert eine minimale SCPI-basierte Kommunikation
    über eine serielle Schnittstelle (RS-232 / USB-Serial).

    @details
    Die Klasse kapselt:

    - Verbindungsaufbau und -abbau
    - SCPI-Schreib- und Abfragebefehle (write/query)
    - Identifikationsabfrage (*IDN?)
    - Gerätereinitialisierung (*RST)
    - Hochgeschwindigkeits-Messsequenz (fastjob)

    Die Methode fastjob() entspricht dem „Programming example C-2“
    des Model 6485/6487 User’s Manual und konfiguriert das Gerät
    für schnelle, gepufferte Strommessungen mit interner
    Datenspeicherung.

    Die Klasse enthält bewusst keine Datenverarbeitung oder
    Visualisierung. Sie stellt ausschließlich die Hardware-
    Kommunikationsschicht dar.
    
    @param port       Serieller Port (z. B. "COM3")
    @param baudrate   Baudrate der seriellen Verbindung (Standard: 9600)
    @param timeout    Lese-Timeout in Sekunden (Standard: 2 s)
    """
    
    def __init__(self, port, baudrate=9600, timeout=2):
        """
        @brief Initialisiert die Keithley-Instanz.
    
        @details
        Speichert die Verbindungsparameter für die serielle Kommunikation,
        öffnet jedoch noch keine Verbindung. Die eigentliche Verbindung
        wird erst durch Aufruf von connect() hergestellt.
    
        @param port
            Serieller Port des Geräts (z. B. "COM3").
    
        @param baudrate
            Baudrate der seriellen Schnittstelle in Bit/s.
            Standardwert: 9600.
    
        @param timeout
            Lese-Timeout der seriellen Verbindung in Sekunden.
            Standardwert: 2 s.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connected = False

    def connect(self):
        """
        @brief Baut die serielle Verbindung zum Keithley 6485 auf.
    
        @details
        Öffnet den konfigurierten seriellen Port mit den zuvor
        gesetzten Kommunikationsparametern (Port, Baudrate, Timeout).
        Nach erfolgreichem Öffnen wird das Attribut `connected`
        auf True gesetzt.
    
        Eine kurze Wartezeit von 0.2 s wird eingefügt, um dem
        Gerät Zeit zur Stabilisierung der Verbindung zu geben.
    
        @exception serial.SerialException
            Falls der Port nicht geöffnet werden kann.
        """
        self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        time.sleep(0.2)
        self.connected = True

    def disconnect(self):
        """
        @brief Trennt die serielle Verbindung zum Gerät.
    
        @details
        Schließt den aktuell geöffneten seriellen Port, sofern
        eine Verbindung besteht. Das Attribut `ser` wird auf None
        gesetzt und der Verbindungsstatus `connected` auf False.
    
        Die Methode ist sicher aufrufbar, auch wenn keine
        aktive Verbindung besteht.
        """
        if self.ser is not None:
            self.ser.close()
            self.ser = None
        self.connected = False

    def write(self, cmd):
        """
        @brief Sendet einen SCPI-Befehl an das Gerät.
    
        @details
        Überträgt einen ASCII-SCPI-Befehl über die serielle
        Schnittstelle an das Gerät. Der Befehl wird automatisch
        mit CR+LF ("\r\n") terminiert und als Byte-String
        kodiert übertragen. Bei der seriellen Kommunikation mit dem 
        Keithley 6485 müssen SCPI-Befehle als Byte-Sequenzen übertragen 
        werden. In Python werden Zeichenketten jedoch standardmäßig als 
        Unicode-Strings repräsentiert. 
        Die Methode `.encode()` wandelt einen String in eine
        Byte-Sequenz um. Dadurch kann der Befehl über die serielle
        Schnittstelle gesendet werden.        
        Beispiel:        
            cmd = "READ?"
            cmd_bytes = cmd.encode()        
        Ergebnis:        
            b'READ?'        
        In der write()-Methode wird zusätzlich ein Zeilenende
        ("\r\n" = Carriage Return + Line Feed) angehängt, da
        Keithley-Geräte dieses Terminierungszeichen für SCPI-
        Befehle erwarten.        
        Das Gegenstück zu `.encode()` ist `.decode()`, das eine
        empfangene Byte-Sequenz wieder in einen lesbaren
        Unicode-String umwandelt.
    
        @param cmd
            SCPI-Befehl als Zeichenkette (ohne Zeilenende).
    
        @exception RuntimeError
            Falls keine aktive Verbindung besteht.
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.ser.write((cmd + "\r\n").encode())

    def query(self, cmd):
        """
        @brief Sendet einen SCPI-Abfragebefehl und liest die Antwort ein.
    
        @details
        Überträgt einen SCPI-Befehl an das Gerät und liest die
        zugehörige Antwort zeilenweise von der seriellen
        Schnittstelle ein.
    
        Vor dem Senden wird der Eingabepuffer mit
        `reset_input_buffer()` gelöscht, um sicherzustellen,
        dass keine alten oder unvollständigen Daten aus
        vorherigen Kommunikationsvorgängen verarbeitet werden.
    
        Die empfangenen Bytes werden in einen Unicode-String
        dekodiert und von führenden bzw. nachfolgenden
        Leerzeichen und Zeilenumbrüchen bereinigt.
    
        @param cmd
            SCPI-Abfragebefehl als Zeichenkette (z. B. "*IDN?").
    
        @return
            Antwort des Geräts als bereinigte Zeichenkette.
    
        @exception RuntimeError
            Falls keine aktive Verbindung besteht.
        """
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.ser.reset_input_buffer()      # <-- wichtig
        self.write(cmd)
        return self.ser.readline().decode(errors="ignore").strip()

    def idn(self):
        """
        @brief Fragt die Geräteidentifikation ab.
    
        @details
        Sendet den standardisierten SCPI-Befehl "*IDN?" an das
        Gerät und gibt die Identifikationszeichenkette zurück.
    
        Die Antwort enthält typischerweise Hersteller,
        Modellbezeichnung, Seriennummer und Firmware-Version.
    
        @return
            Identifikationsstring des Geräts.
    
        @exception RuntimeError
            Falls keine aktive Verbindung besteht.
        """
        return self.query("*IDN?")
    
    def reset(self):
        """
        @brief Setzt das Gerät auf den definierten Reset-Zustand zurück.
    
        @details
        Sendet den SCPI-Befehl "*RST" an das Gerät. Dadurch werden
        die meisten Geräteeinstellungen auf ihre Standardwerte
        zurückgesetzt.
    
        Der Reset betrifft unter anderem Trigger-, Mess- und
        Anzeigeeinstellungen. Eine bestehende serielle Verbindung
        bleibt davon unberührt.
    
        @exception RuntimeError
            Falls keine aktive Verbindung besteht.
        """
        self.write("*RST")    
        
    def fastjob(self, n=100, nplc=0.01, rang=0.002):
        self.write("*RST")
        self.write("TRIG:DEL 0")
        self.write(f"TRIG:COUN {n}")
        self.write(f"NPLC {nplc}")
        #self.write(f"RANG {rang}")            # Range fest vorgegeben
        self.write("SENS:CURR:RANG:AUTO ON")   # Autorange
        self.write("SYST:ZCH OFF")
        self.write("SYST:AZER:STAT OFF")        
        self.write("DISP:ENAB OFF")
        self.write("*CLS")    
        self.write(f"TRAC:POIN {n}")
        self.write("TRAC:CLE")
        self.write("TRAC:FEED:CONT NEXT")    
        self.write("STAT:MEAS:ENAB 512")
        self.write("*SRE 1")    
        # Synchronisieren mit Konfig fertig? _ = steht für eine Wegwerfvariable
        _ = self.query("*OPC?")        
        self.write("FORM:ELEM READ,TIME,STAT")    
        # Messung starten
        self.write("INIT")        
        self.write("DISP:ENAB ON")        
        old_timeout = self.ser.timeout
        self.ser.timeout = 10
        try:
            data = self.query("TRAC:DATA?")
        finally:
            self.ser.timeout = old_timeout    
        return data

                                 
def print_banner() -> None:   
    """
    @brief Gibt ein formatiertes Programm-Banner auf der Konsole aus.

    @details
    Erzeugt mit `pyfiglet` einen ASCII-Art-Titel und gibt
    diesen farbig formatiert in der Konsole aus. Zusätzlich
    werden Versionsinformation und Institutszugehörigkeit
    angezeigt.

    Die Farbcodierung erfolgt über ANSI-Escape-Sequenzen.
    Mit `colorama.init()` wird sichergestellt, dass die
    Farbdarstellung auch unter Windows korrekt funktioniert.

    Die Funktion dient ausschließlich der optischen
    Darstellung beim Programmstart und besitzt keinen
    Einfluss auf die Gerätekommunikation.
    """
    init()
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    banner = figlet_format("Keithley Control", font="slant")
    subtitle = """
Version 1.1
JLU Giessen – IPI
"""
    print(GREEN + banner + RESET)
    print(CYAN + subtitle + RESET)
    print("-" * 80)


def parse_data(data_str):
    """
    @brief Wandelt die vom Keithley zurückgegebenen Trace-Daten in NumPy-Arrays um.

    @details
    Erwartet eine durch Kommas getrennte ASCII-Zeichenkette,
    wie sie von `TRAC:DATA?` geliefert wird, mit der Struktur:

        READ, TIME, STAT, READ, TIME, STAT, ...

    Zunächst wird die Einheit "A" aus den Stromwerten entfernt.
    Anschließend werden die Daten mit `numpy.fromstring` in ein
    Float-Array konvertiert und in eine 2D-Struktur mit drei
    Spalten reshaped.

    Der erste Datensatz wird verworfen, da dieser häufig
    durch Initialisierungs- oder Triggerverzögerungen
    beeinflusst ist.

    @param data_str
        Rohdatenstring aus `TRAC:DATA?`.

    @return
        Tuple aus drei NumPy-Arrays:
        (time_array, current_array, status_array)
    """
    cleaned = data_str.replace("A", "").strip()
    arr = np.fromstring(cleaned, sep=",", dtype=float)
    data = arr.reshape(-1, 3)
    data = data[1:, :]   # <-- erster Datensatz weg
    return data[:,1], data[:,0], data[:,2]


def plot_data(data_str):
    """
    @brief Visualisiert die gemessenen Trace-Daten grafisch.

    @details
    Wandelt den vom Keithley-Gerät gelieferten Rohdatenstring
    mit `parse_data()` in strukturierte NumPy-Arrays um und
    stellt den Stromverlauf als Funktion der Zeit dar.

    Die Darstellung erfolgt mit Matplotlib als 2D-Plot
    (I über t). Der Statuskanal wird nicht visualisiert,
    steht jedoch weiterhin in den geparsten Daten zur
    Verfügung.

    @param data_str
        Rohdatenstring aus dem SCPI-Befehl `TRAC:DATA?`.
    """
    t, I, s = parse_data(data_str)
    plt.figure()
    plt.plot(t, I, marker="o")
    plt.xlabel("t (s)")
    plt.ylabel("I (A)")
    plt.grid(True)
    plt.show()


def main():
    pico = Keithley6485("COM3")

    try:
        pico.connect()
    except serial.SerialException as e:
        print("Serial-Fehler: ", e)
                        
    idn_string = pico.idn()
    print("IDN: ", idn_string)
            
    pico.reset()
    
    data = pico.fastjob(n=10)
    t,I,s = parse_data(data)
    plot_data(data)
    print(I)  
    pico.disconnect()


def clear_console():
    """
    @brief Löscht die Konsolenausgabe.

    @details
    Führt systemabhängig den entsprechenden Befehl zum
    Leeren der Konsole aus:

    - Unter Windows: "cls"
    - Unter Unix/Linux/macOS: "clear"

    Die Funktion dient ausschließlich der optischen
    Strukturierung der Programmausgabe und hat keinen
    Einfluss auf die Gerätekommunikation.
    """
    os.system("cls" if platform.system() == "Windows" else "clear")



if __name__ == "__main__":
    clear_console()
    print_banner()
    main()
































