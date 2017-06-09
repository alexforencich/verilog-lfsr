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

module = 'lfsr_prbs_gen'
testbench = 'test_%s_prbs9' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("../rtl/lfsr.v")
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def prbs9(state = 0x1ff):
    while True:
        for i in range(8):
            if bool(state & 0x10) ^ bool(state & 0x100):
                state = ((state & 0xff) << 1) | 1
            else:
                state = (state & 0xff) << 1
        yield state & 0xff

def bench():

    # Parameters
    LFSR_WIDTH = 9
    LFSR_POLY = 0x021
    LFSR_INIT = 0x1ff
    LFSR_CONFIG = "FIBONACCI"
    REVERSE = 0
    INVERT = 0
    DATA_WIDTH = 8
    STYLE = "AUTO"

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    enable = Signal(bool(0))

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
        enable=enable,
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
        print("test 1: test PRBS9")
        current_test.next = 1

        gen = prbs9()

        enable.next = 1
        yield clk.posedge
        yield clk.posedge
        enable.next = 0

        rst.next = 1
        yield clk.posedge
        rst.next = 0
        yield clk.posedge

        enable.next = 1
        yield clk.posedge

        for i in range(512):

            ref = next(gen)
            val = data_out.val

            print((ref, val))

            assert ref == val

            yield clk.posedge

        enable.next = 0

        yield delay(100)

        raise StopSimulation

    return dut, clkgen, check

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()
