#
# generiert von Google-KI
# wusste sogar in welcher Zeitzone gefragt wurde (MESZ / MEZ)
# 
import network
import time
import ntptime
from machine import RTC
import secrets_multi

import time
from machine import Pin
import neopixel

#NeoPixel configuration
pin_number    = 19  # GPIO
number_of_led =  1  # only one to blink

np = neopixel.NeoPixel(Pin(pin_number), number_of_led)
#colors
RED_ON   = (200, 0, 0)  # red
GREEN_ON = (0, 200, 0)  # green
LED_OFF  = (0, 0, 0)    # LED off


def wlan_verbinden():
    # WLAN-Interface im Station-Modus aktivieren
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    print("Scanne nach verfügbaren Netzwerken...")
    # Scant die Umgebung. network.scan() gibt Tupel zurück, das erste Element [0] ist die SSID
    verfuegbare_netze = [net[0].decode('utf-8') for net in wlan.scan()]
    print("Gefundene Netzwerke:", verfuegbare_netze)

    # Durchsuche deine Liste aus secrets_multi
    for ssid, passwort in zip(secrets_multi.mySSIDlist, secrets_multi.myPasswordlist):
        if ssid in verfuegbare_netze:
            print(f"Passendes Netzwerk gefunden: {ssid}. Verbindungsversuch...")
            wlan.connect(ssid, passwort)
            
            # Maximal 10 Sekunden auf die Verbindung warten
            versuche = 10
            while versuche > 0 and not wlan.isconnected():
                print("." , versuche)
                for _ in range(1):   # blink 2 x green
                    np[0] = GREEN_ON
                    np.write()  # Die Daten an die LED übertragen
                    time.sleep(0.5)  # 0.5 Sekunden warten
                    np[0] = LED_OFF
                    np.write()  # Die Daten an die LED übertragen
                    time.sleep(0.5)  # 0.5 Sekunden warten                
		time.sleep(5)
                versuche -= 1
                
            if wlan.isconnected():
                print(f"Erfolgreich verbunden! IP-Adresse: {wlan.ifconfig()[0]}")
                return True
            else:
                print(f"Verbindung mit {ssid} fehlgeschlagen.")
                np[0] = RED_ON
                np.write()
                
    print("Keines deiner gespeicherten Netzwerke ist in Reichweite.")
    return False


def get_cest_offset(utc_tuple):
    """Berechnet, ob Sommerzeit (MESZ = +2h) oder Winterzeit (MEZ = +1h) aktiv ist."""
    year = utc_tuple[0]
    
    # Formel zur Berechnung des letzten Sonntags im März und Oktober
    march_last = 31 - (int(5 * year / 4 + 4) % 7)
    oct_last = 31 - (int(5 * year / 4 + 1) % 7)
    
    # Zeitpunkte für die Umstellung in Sekunden (jeweils 01:00 UTC)
    t_march = time.mktime((year, 3, march_last, 1, 0, 0, 0, 0))
    t_oct = time.mktime((year, 10, oct_last, 1, 0, 0, 0, 0))
    
    # Aktuelle UTC-Zeit in Sekunden umwandeln
    t_utc = time.mktime(utc_tuple)
    
    # Wenn innerhalb der Sommerzeit: +2 Stunden (7200s), sonst +1 Stunde (3600s)
    if t_march <= t_utc < t_oct:
        print('Summertime')
        return 7200  # MESZ
    else:
        print('Wintertime')
        return 3600  # MEZ

def sync_time():
    """Holt UTC via NTP, berechnet die lokale Zeit und stellt die Pico RTC ein."""
    try:
        # NTP-Zeit abrufen (setzt die MicroPython-Systemzeit standardmässig auf UTC)
        print("Synchronisiere Zeit via NTP...")
        ntptime.host = "pool.ntp.org"
        ntptime.settime()
        
        # Aktuelle UTC-Zeit auslesen
        utc_now = time.gmtime()
        print("habe utc_now ...")
        
        # Lokalen Offset berechnen (MEZ oder MESZ)
        offset_seconds = get_cest_offset(utc_now)
        
        # Lokale Zeit berechnen
        local_seconds = time.mktime(utc_now) + offset_seconds
        l = time.localtime(local_seconds) # (Jahr, Monat, Tag, Stunde, Minute, Sekunde, Wochentag, Jahrestag)
        
        # Interne Pico RTC konfigurieren
        # RTC benötigt das Format: (Jahr, Monat, Tag, Wochentag, Stunde, Minute, Sekunde, Subsekunde)
        # Hinweis: MicroPython time Wochentag ist 0-6 (Mo-So), RTC erwartet oft 1-7 oder ignoriert es.
        rtc = RTC()
        rtc.datetime((l[0], l[1], l[2], l[6], l[3], l[4], l[5], 0))
        
        print("Uhrzeit erfolgreich synchronisiert!")
    except Exception as e:
        print("Fehler bei der Zeitsynchronisation:", e)

# Hauptprogramm
wlan_verbinden()

sync_time()

print("\nLokale Uhrzeit auf dem Pico W:")
rtc = RTC()
t = rtc.datetime()
# Formatierte Ausgabe: DD.MM.YYYY HH:MM:SS
print(f"{t[2]:02d}.{t[1]:02d}.{t[0]} {t[4]:02d}:{t[5]:02d}:{t[6]:02d}")


