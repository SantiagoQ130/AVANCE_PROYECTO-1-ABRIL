import struct
import utime
from machine import Pin, SPI, I2C
from nrf24l01 import NRF24L01
import ssd1306

# Pines NRF24L01
SPI_ID = 0
SCK = 2
MOSI = 3
MISO = 4
CSN = 5
CE = 6

# Pines I2C para OLED
SDA = 14
SCL = 15
WIDTH = 128
HEIGHT = 64

# Direcciones TX
TX_ADDRESSES = {
    1: b"\xe1\xf0\xf0\xf0\xf0",
    2: b"\xc3\xf0\xf0\xf0\xf0",
    3: b"\xd2\xf0\xf0\xf0\xf0"  # NUEVA dirección para TX3
}

# Configurar OLED
i2c = I2C(1, scl=Pin(SCL), sda=Pin(SDA))
oled = ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)

# Variables globales
last_rssi = {1: -100, 2: -100, 3: -100}
led = Pin("LED", Pin.OUT)

def setup_nrf():
    spi = SPI(SPI_ID, sck=Pin(SCK), mosi=Pin(MOSI), miso=Pin(MISO))
    csn = Pin(CSN, Pin.OUT, value=1)
    ce = Pin(CE, Pin.OUT, value=0)

    nrf = NRF24L01(spi, csn, ce, payload_size=8)
    nrf.set_channel(21)

    for pipe, addr in TX_ADDRESSES.items():
        nrf.open_rx_pipe(pipe, addr)

    return nrf

def mostrar_oled():
    oled.fill(0)
    oled.text("RSSI Recibido", 0, 0)
    oled.text(f"TX1: {last_rssi[1]} dBm", 0, 15)
    oled.text(f"TX2: {last_rssi[2]} dBm", 0, 30)
    oled.text(f"TX3: {last_rssi[3]} dBm", 0, 45)
    oled.show()

def receiver_loop(nrf):
    nrf.start_listening()
    print("Receptor activo...")

    while True:
        if nrf.any():
            led.on()
            try:
                buf = nrf.recv()
                if len(buf) == 8:
                    message_id, rssi = struct.unpack("ii", buf)
                    if message_id in last_rssi:
                        last_rssi[message_id] = rssi
                        print(f"TX{message_id} -> {rssi} dBm")
                        mostrar_oled()
                    else:
                        print(f"ID desconocido: {message_id}")
                else:
                    print(f"Payload inesperado: {len(buf)} bytes")
            except Exception as e:
                print(f"Error al leer: {e}")
            led.off()
        utime.sleep_ms(5)

def main():
    try:
        nrf = setup_nrf()
        mostrar_oled()
        receiver_loop(nrf)
    except Exception as e:
        print(f"Error en el receptor: {e}")

if __name__ == "__main__":
    main()
