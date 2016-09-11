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
import struct

module = 'lfsr_scramble'
testbench = 'test_%s_64' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("../rtl/lfsr.v")
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def scramble_64b66b(data, state=0x3ffffffffffffff):
    data_out = bytearray()
    for d in data:
        b = 0
        for i in range(8):
            if bool(state & (1<<38)) ^ bool(state & (1<<57)) ^ bool(d & (1 << i)):
                state = ((state & 0x1ffffffffffffff) << 1) | 1
                b = b | (1 << i)
            else:
                state = (state & 0x1ffffffffffffff) << 1
        data_out += bytearray([b])
    return data_out

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]

def bench():

    # Parameters
    LFSR_WIDTH = 58
    LFSR_POLY = 0x8000000001
    LFSR_INIT = 0x3ffffffffffffff
    LFSR_CONFIG = "FIBONACCI"
    REVERSE = 1
    DATA_WIDTH = 64
    STYLE = "AUTO"

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    data_in = Signal(intbv(0)[DATA_WIDTH:])
    data_in_valid = Signal(bool(0))

    # Outputs
    data_out = Signal(intbv(0)[DATA_WIDTH:])

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
        data_out=data_out
    )

    @always(delay(4))
    def clkgen():
        clk.next = not clk

    @instance
    def check():
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
        print("test 1: block")
        current_test.next = 1

        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge

        block = bytes(range(256))

        scr = scramble_64b66b(block)

        for i in range(0, len(block), 8):
            data_in.next = struct.unpack('<Q', block[i:i+8])[0]
            data_in_valid.next = 1
            yield clk.posedge
            if i > 0:
                ref = struct.unpack('<Q', scr[i-8:i])[0]
                print(hex(data_out))
                print(hex(ref))
                assert data_out == ref
            i += 8
        data_in_valid.next = 0
        yield clk.posedge

        yield delay(100)

        raise StopSimulation

    return dut, clkgen, check

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
