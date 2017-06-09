#!/usr/bin/env python
"""

Copyright (c) 2016 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from myhdl import *
import os
import zlib

module = 'lfsr_crc'
testbench = 'test_%s_crc32' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("../rtl/lfsr.v")
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def bench():

    # Parameters
    LFSR_WIDTH = 32
    LFSR_POLY = 0x04c11db7
    LFSR_INIT = 0xffffffff
    LFSR_CONFIG = "GALOIS"
    REVERSE = 1
    INVERT = 1
    DATA_WIDTH = 8
    STYLE = "AUTO"

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    data_in = Signal(intbv(0)[DATA_WIDTH:])
    data_in_valid = Signal(bool(0))

    # Outputs
    crc_out = Signal(intbv(0)[LFSR_WIDTH:])

    # DUT
    if os.system(build_cmd):
        raise Exception("Error running build command")

    dut = Cosimulation(
        "vvp -m myhdl %s.vvp -lxt2" % testbench,
        clk=clk,
        rst=rst,
        current_test=current_test,
        data_in=data_in,
        data_in_valid=data_in_valid,
        crc_out=crc_out
    )

    @always(delay(4))
    def clkgen():
        clk.next = not clk

    @instance
    def check():
        print("mark")
        yield delay(100)
        yield clk.posedge
        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge
        yield delay(100)
        yield clk.posedge

        # testbench stimulus

        yield clk.posedge
        print("test 1: single word")
        current_test.next = 1

        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge

        data_in.next = 0x12
        data_in_valid.next = 1
        yield clk.posedge
        data_in_valid.next = 0
        yield clk.posedge

        print(hex(crc_out.val))
        print(hex(zlib.crc32(b'\x12') & 0xffffffff))

        assert crc_out.val == zlib.crc32(b'\x12') & 0xffffffff

        yield delay(100)

        yield clk.posedge
        print("test 2: block")
        current_test.next = 2

        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge

        block = b'\x11\x22\x33\x44'

        for b in block:
            data_in.next = b
            data_in_valid.next = 1
            yield clk.posedge
        data_in_valid.next = 0
        yield clk.posedge

        print(hex(crc_out.val))
        print(hex(zlib.crc32(block) & 0xffffffff))

        assert crc_out.val == zlib.crc32(block) & 0xffffffff

        yield delay(100)

        raise StopSimulation

    return dut, clkgen, check

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
