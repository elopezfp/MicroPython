import time
from machine import Pin
import framebuf

class ILI9341:
    def __init__(self, spi, cs, dc, rst, width=320, height=240):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.width = width
        self.height = height
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=1)
        self.reset()
        self.init()

    def write_cmd(self, cmd):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, data):
        self.dc(1)
        self.cs(0)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs(1)

    def reset(self):
        self.rst(0)
        time.sleep_ms(50)
        self.rst(1)
        time.sleep_ms(50)

    def init(self):
        for cmd, data in (
            (0xEF, b'\x03\x80\x02'),
            (0xCF, b'\x00\xc1\x30'),
            (0xED, b'\x64\x03\x12\x81'),
            (0xE8, b'\x85\x00\x78'),
            (0xCB, b'\x39\x2c\x00\x34\x02'),
            (0xF7, b'\x20'),
            (0xEA, b'\x00\x00'),
            (0xC0, b'\x23'),
            (0xC1, b'\x10'),
            (0xC5, b'\x3e\x28'),
            (0xC7, b'\x86'),
            (0x36, b'\xE8'), # Landscape invertido (MY+MX+MV+BGR) para mejor lectura
            (0x3A, b'\x55'),
            (0xB1, b'\x00\x18'),
            (0xB6, b'\x08\x82\x27'),
            (0xF2, b'\x00'),
            (0x26, b'\x01'),
            (0xE0, b'\x0F\x31\x2B\x0C\x0E\x08\x4E\xF1\x37\x07\x10\x03\x0E\x09\x00'),
            (0xE1, b'\x00\x0E\x14\x03\x11\x07\x31\xC1\x48\x08\x0F\x0C\x31\x36\x0F'),
            (0x11, None),
            (0x29, None),
        ):
            self.write_cmd(cmd)
            if data:
                self.write_data(data)
        time.sleep_ms(120)

    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(0x2A)
        self.write_data(bytearray([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self.write_cmd(0x2B)
        self.write_data(bytearray([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self.write_cmd(0x2C)

    def fill_rect(self, x, y, w, h, color):
        self.set_window(x, y, x + w - 1, y + h - 1)
        chunks, rest = divmod(w * h, 512)
        c_buf = bytearray([color >> 8, color & 0xFF] * 512)
        self.dc(1)
        self.cs(0)
        if chunks:
            for _ in range(chunks):
                self.spi.write(c_buf)
        if rest:
            self.spi.write(bytearray([color >> 8, color & 0xFF] * rest))
        self.cs(1)
        
    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)
        
    def text(self, text, x, y, color, scale=1):
        w = len(text) * 8
        h = 8
        buf = bytearray((w * h) // 8)
        fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_VLSB)
        fb.fill(0)
        fb.text(text, 0, 0, 1)
        for py in range(h):
            for px in range(w):
                # fb.pixel is safer than manual bit math
                if fb.pixel(px, py):
                    self.fill_rect(x + px * scale, y + py * scale, scale, scale, color)
