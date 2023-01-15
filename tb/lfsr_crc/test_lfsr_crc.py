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
import zlib

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

        dut.data_in.setimmediatevalue(0)
        dut.data_in_valid.setimmediatevalue(0)

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


def crc32(data):
    return zlib.crc32(data) & 0xffffffff


async def run_test_crc(dut, ref_crc):

    data_width = len(dut.data_in)
    byte_lanes = data_width // 8

    tb = TB(dut)

    await tb.reset()

    block = bytes([(x+1)*0x11 for x in range(byte_lanes)])

    dut.data_in.value = int.from_bytes(block, 'little')
    dut.data_in_valid.value = 1
    await RisingEdge(dut.clk)
    dut.data_in_valid.value = 0

    await RisingEdge(dut.clk)
    val = dut.crc_out.value.integer
    ref = ref_crc(block)

    tb.log.info("CRC: 0x%x (ref: 0x%x)", val, ref)

    assert val == ref

    await tb.reset()

    block = bytearray(itertools.islice(itertools.cycle(range(256)), 1024))

    for b in chunks(block, byte_lanes):
        dut.data_in.value = int.from_bytes(b, 'little')
        dut.data_in_valid.value = 1
        await RisingEdge(dut.clk)
    dut.data_in_valid.value = 0

    await RisingEdge(dut.clk)
    val = dut.crc_out.value.integer
    ref = ref_crc(block)

    tb.log.info("CRC: 0x%x (ref: 0x%x)", val, ref)

    assert val == ref

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)


if cocotb.SIM_NAME:

    if cocotb.top.LFSR_POLY.value == 0x4c11db7:
        factory = TestFactory(run_test_crc)
        factory.add_option("ref_crc", [crc32])
        factory.generate_tests()


# cocotb-test

tests_dir = os.path.abspath(os.path.dirname(__file__))
rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', '..', 'rtl'))


@pytest.mark.parametrize(("lfsr_width", "lfsr_poly", "lfsr_init", "lfsr_config", "reverse", "invert", "data_width"), [
            (32, "32'h4c11db7", "32'hffffffff", "\"GALOIS\"", 1, 1, 8),
            (32, "32'h4c11db7", "32'hffffffff", "\"GALOIS\"", 1, 1, 64),
        ])
def test_lfsr_crc(request, lfsr_width, lfsr_poly, lfsr_init, lfsr_config, reverse, invert, data_width):
    dut = "lfsr_crc"
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
    parameters['LFSR_CONFIG'] = lfsr_config
    parameters['REVERSE'] = reverse
    parameters['INVERT'] = invert
    parameters['DATA_WIDTH'] = data_width
    parameters['STYLE'] = "\"AUTO\""

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
