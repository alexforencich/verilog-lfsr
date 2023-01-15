#!/usr/bin/env python
"""

Copyright (c) 2023 Alex Forencich

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

import itertools
import logging
import os

import pytest
import cocotb_test.simulator

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.regression import TestFactory


class TB:
    def __init__(self, dut):
        self.dut = dut

        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

        dut.enable.setimmediatevalue(0)

    async def reset(self):
        self.dut.rst.setimmediatevalue(0)
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst.value = 1
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)
        self.dut.rst.value = 0
        await RisingEdge(self.dut.clk)
        await RisingEdge(self.dut.clk)


def chunks(lst, n, padvalue=None):
    return itertools.zip_longest(*[iter(lst)]*n, fillvalue=padvalue)


def prbs9(state=0x1ff):
    while True:
        for i in range(8):
            if bool(state & 0x10) ^ bool(state & 0x100):
                state = ((state & 0xff) << 1) | 1
            else:
                state = (state & 0xff) << 1
        yield ~state & 0xff


def prbs31(state=0x7fffffff):
    while True:
        for i in range(8):
            if bool(state & 0x08000000) ^ bool(state & 0x40000000):
                state = ((state & 0x3fffffff) << 1) | 1
            else:
                state = (state & 0x3fffffff) << 1
        yield ~state & 0xff


async def run_test_prbs(dut, ref_prbs):

    data_width = len(dut.data_out)
    byte_lanes = data_width // 8

    tb = TB(dut)

    await tb.reset()

    gen = chunks(ref_prbs(), byte_lanes)

    dut.enable.value = 1
    await RisingEdge(dut.clk)

    for i in range(512):
        ref = int.from_bytes(bytes(next(gen)), 'big')
        val = dut.data_out.value.integer

        tb.log.info("PRBS: 0x%x (ref: 0x%x)", val, ref)

        assert ref == val

        await RisingEdge(dut.clk)


if cocotb.SIM_NAME:

    if cocotb.top.LFSR_POLY.value == 0x021:
        factory = TestFactory(run_test_prbs)
        factory.add_option("ref_prbs", [prbs9])
        factory.generate_tests()

    if cocotb.top.LFSR_POLY.value == 0x10000001:
        factory = TestFactory(run_test_prbs)
        factory.add_option("ref_prbs", [prbs31])
        factory.generate_tests()


# cocotb-test

tests_dir = os.path.abspath(os.path.dirname(__file__))
rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', '..', 'rtl'))


@pytest.mark.parametrize("style", ["AUTO", "LOOP"])
@pytest.mark.parametrize(("lfsr_width", "lfsr_poly", "lfsr_init", "lfsr_config", "reverse", "invert", "data_width"), [
            (9,  "9'h021", "9'h1ff", "FIBONACCI", 0, 1, 8),
            (9,  "9'h021", "9'h1ff", "FIBONACCI", 0, 1, 64),
            (31, "31'h10000001", "31'h7fffffff", "FIBONACCI", 0, 1, 8),
            (31, "31'h10000001", "31'h7fffffff", "FIBONACCI", 0, 1, 64),
        ])
def test_lfsr_prbs_gen(request, lfsr_width, lfsr_poly, lfsr_init, lfsr_config, reverse, invert, data_width, style):
    dut = "lfsr_prbs_gen"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut

    verilog_sources = [
        os.path.join(rtl_dir, f"{dut}.v"),
        os.path.join(rtl_dir, "lfsr.v"),
    ]

    parameters = {}

    parameters['LFSR_WIDTH'] = lfsr_width
    parameters['LFSR_POLY'] = lfsr_poly
    parameters['LFSR_INIT'] = lfsr_init
    parameters['LFSR_CONFIG'] = f'"{lfsr_config}"'
    parameters['REVERSE'] = reverse
    parameters['INVERT'] = invert
    parameters['DATA_WIDTH'] = data_width
    parameters['STYLE'] = f'"{style}"'

    extra_env = {f'PARAM_{k}': str(v) for k, v in parameters.items()}

    sim_build = os.path.join(tests_dir, "sim_build",
        request.node.name.replace('[', '-').replace(']', ''))

    cocotb_test.simulator.run(
        python_search=[tests_dir],
        verilog_sources=verilog_sources,
        toplevel=toplevel,
        module=module,
        parameters=parameters,
        sim_build=sim_build,
        extra_env=extra_env,
    )
