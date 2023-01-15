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


def scramble_64b66b(data, state=0x3ffffffffffffff):
    data_out = bytearray()
    for d in data:
        b = 0
        for i in range(8):
            if bool(state & (1 << 38)) ^ bool(state & (1 << 57)) ^ bool(d & (1 << i)):
                state = ((state & 0x1ffffffffffffff) << 1) | 1
                b = b | (1 << i)
            else:
                state = (state & 0x1ffffffffffffff) << 1
        data_out.append(b)
    return data_out


def descramble_64b66b(data, state=0x3ffffffffffffff):
    data_out = bytearray()
    for d in data:
        b = 0
        for i in range(8):
            if bool(state & (1 << 38)) ^ bool(state & (1 << 57)) ^ bool(d & (1 << i)):
                b = b | (1 << i)
            state = (state & 0x1ffffffffffffff) << 1 | bool(d & (1 << i))
        data_out += bytearray([b])
    return data_out


async def run_test_descramble(dut, ref_scramble):

    data_width = len(dut.data_in)
    byte_lanes = data_width // 8

    tb = TB(dut)

    await tb.reset()

    block = bytearray(itertools.islice(itertools.cycle(range(256)), 1024))

    scr = scramble_64b66b(block)

    dscr = descramble_64b66b(scr)

    assert dscr == block

    ref_iter = iter(chunks(block, byte_lanes))

    first = True
    for b in chunks(scr, byte_lanes):
        dut.data_in.value = int.from_bytes(b, 'little')
        dut.data_in_valid.value = 1
        await RisingEdge(dut.clk)

        val = dut.data_out.value.integer

        if not first:
            ref = int.from_bytes(bytes(next(ref_iter)), 'little')

            tb.log.info("Descrambled: 0x%x (ref: 0x%x)", val, ref)

            assert ref == val

        first = False

    dut.data_in_valid.value = 0

    await RisingEdge(dut.clk)


if cocotb.SIM_NAME:

    # if cocotb.top.LFSR_POLY.value == 0x8000000001:
    if cocotb.top.LFSR_WIDTH == 58:
        factory = TestFactory(run_test_descramble)
        factory.add_option("ref_scramble", [scramble_64b66b])
        factory.generate_tests()


# cocotb-test

tests_dir = os.path.abspath(os.path.dirname(__file__))
rtl_dir = os.path.abspath(os.path.join(tests_dir, '..', '..', 'rtl'))


@pytest.mark.parametrize("style", ["AUTO", "LOOP"])
@pytest.mark.parametrize(("lfsr_width", "lfsr_poly", "lfsr_init", "lfsr_config", "reverse", "data_width"), [
            (58,  "58'h8000000001", "58'h3ffffffffffffff", "FIBONACCI", 1, 8),
            (58,  "58'h8000000001", "58'h3ffffffffffffff", "FIBONACCI", 1, 64),
        ])
def test_lfsr_descramble(request, lfsr_width, lfsr_poly, lfsr_init, lfsr_config, reverse, data_width, style):
    dut = "lfsr_descramble"
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
