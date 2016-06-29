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

module = 'lfsr'
testbench = 'test_%s_prbs31' % module

srcs = []

srcs.append("../rtl/%s.v" % module)
srcs.append("%s.v" % testbench)

src = ' '.join(srcs)

build_cmd = "iverilog -o %s.vvp %s" % (testbench, src)

def dut_lfsr(clk,
             rst,
             current_test,
             data_in,
             lfsr_in,
             lfsr_out):

    if os.system(build_cmd):
        raise Exception("Error running build command")
    return Cosimulation("vvp -m myhdl %s.vvp -lxt2" % testbench,
                clk=clk,
                rst=rst,
                current_test=current_test,
                data_in=data_in,
                lfsr_in=lfsr_in,
                lfsr_out=lfsr_out)

def prbs31(state = 0x7fffffff):
    while True:
        for i in range(8):
            if bool(state & 0x08000000) ^ bool(state & 0x40000000):
                state = ((state & 0x3fffffff) << 1) | 1
            else:
                state = (state & 0x3fffffff) << 1
        yield state & 0xff

def bench():

    # Parameters
    LFSR_WIDTH = 31
    LFSR_POLY = 0x10000001
    LFSR_CONFIG = "FIBONACCI"
    REVERSE = 0
    DATA_WIDTH = 8
    OUTPUT_WIDTH = max(DATA_WIDTH, LFSR_WIDTH)
    STYLE = "AUTO"

    # Inputs
    clk = Signal(bool(0))
    rst = Signal(bool(0))
    current_test = Signal(intbv(0)[8:])

    data_in = Signal(intbv(0)[DATA_WIDTH:])
    lfsr_in = Signal(intbv(0)[LFSR_WIDTH:])

    # Outputs
    lfsr_out = Signal(intbv(0)[OUTPUT_WIDTH:])

    # DUT
    dut = dut_lfsr(clk,
                   rst,
                   current_test,
                   data_in,
                   lfsr_in,
                   lfsr_out)

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
        print("test 1: test PRBS31")
        current_test.next = 1

        lfsr_in.next = 0x7fffffff
        data_in.next = 0
        gen = prbs31()

        for i in range(512):

            yield clk.posedge

            ref = next(gen)
            val = lfsr_out[DATA_WIDTH:]

            print((ref, val))

            assert ref == val

            lfsr_in.next = lfsr_out.val[OUTPUT_WIDTH:OUTPUT_WIDTH-LFSR_WIDTH]

        yield delay(100)

        raise StopSimulation

    return dut, clkgen, check

def test_bench():
    sim = Simulation(bench())
    sim.run()

if __name__ == '__main__':
    print("Running test...")
    test_bench()