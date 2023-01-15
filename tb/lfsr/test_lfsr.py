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
from cocotb.triggers import Timer
from cocotb.regression import TestFactory


class TB:
    def __init__(self, dut):
        self.dut = dut

        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        dut.data_in.setimmediatevalue(0)
        dut.state_in.setimmediatevalue(0)


def chunks(lst, n, padvalue=None):
    return itertools.zip_longest(*[iter(lst)]*n, fillvalue=padvalue)


def crc32(data):
    return zlib.crc32(data) & 0xffffffff


def crc32c(data, crc=0xffffffff, poly=0x82f63b78):
    for d in data:
        crc = crc ^ d
        for bit in range(0, 8):
            if crc & 1:
                crc = (crc >> 1) ^ poly
            else:
                crc = crc >> 1
    return ~crc & 0xffffffff


async def run_test_crc(dut, ref_crc):

    data_width = len(dut.data_in)
    byte_lanes = data_width // 8

    state_width = len(dut.state_in)
    state_mask = 2**state_width-1

    tb = TB(dut)

    await Timer(10, 'ns')

    block = bytes([(x+1)*0x11 for x in range(byte_lanes)])

    dut.state_in.value = state_mask
    dut.data_in.value = int.from_bytes(block, 'little')
    await Timer(10, 'ns')

    val = ~dut.state_out.value.integer & state_mask
    ref = ref_crc(block)

    tb.log.info("CRC: 0x%x (ref: 0x%x)", val, ref)

    assert val == ref

    await Timer(10, 'ns')

    block = bytearray(itertools.islice(itertools.cycle(range(256)), 1024))

    dut.state_in.value = state_mask
    for b in chunks(block, byte_lanes):
        dut.data_in.value = int.from_bytes(b, 'little')
        await Timer(10, 'ns')
        dut.state_in.value = dut.state_out.value

    val = ~dut.state_out.value.integer & state_mask
    ref = ref_crc(block)

    tb.log.info("CRC: 0x%x (ref: 0x%x)", val, ref)

    assert val == ref

    await Timer(10, 'ns')


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

    data_width = len(dut.data_in)
    byte_lanes = data_width // 8
    data_mask = 2**data_width-1

    state_width = len(dut.state_in)
    state_mask = 2**state_width-1

    tb = TB(dut)

    await Timer(10, 'ns')

    dut.state_in.value = state_mask
    dut.data_in.value = 0
    gen = chunks(ref_prbs(), byte_lanes)

    await Timer(10, 'ns')

    for i in range(512):
        ref = int.from_bytes(bytes(next(gen)), 'big')
        val = ~dut.data_out.value.integer & data_mask

        tb.log.info("PRBS: 0x%x (ref: 0x%x)", val, ref)

        assert ref == val

        dut.state_in.value = dut.state_out.value

        await Timer(10, 'ns')


if cocotb.SIM_NAME:

    if cocotb.top.LFSR_POLY.value == 0x4c11db7:
        factory = TestFactory(run_test_crc)
        factory.add_option("ref_crc", [crc32])
        factory.generate_tests()

    if cocotb.top.LFSR_POLY.value == 0x1edc6f41:
        factory = TestFactory(run_test_crc)
        factory.add_option("ref_crc", [crc32c])
        factory.generate_tests()

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


@pytest.mark.parametrize(("lfsr_width", "lfsr_poly", "lfsr_config", "reverse", "data_width"), [
            (32, "32'h4c11db7", "\"GALOIS\"", 1, 8),
            (32, "32'h4c11db7", "\"GALOIS\"", 1, 64),
            (32, "32'h1edc6f41", "\"GALOIS\"", 1, 8),
            (32, "32'h1edc6f41", "\"GALOIS\"", 1, 64),
            (9,  "9'h021", "\"FIBONACCI\"", 0, 8),
            (9,  "9'h021", "\"FIBONACCI\"", 0, 64),
            (31, "31'h10000001", "\"FIBONACCI\"", 0, 8),
            (31, "31'h10000001", "\"FIBONACCI\"", 0, 64),
        ])
def test_lfsr(request, lfsr_width, lfsr_poly, lfsr_config, reverse, data_width):
    dut = "lfsr"
    module = os.path.splitext(os.path.basename(__file__))[0]
    toplevel = dut

    verilog_sources = [
        os.path.join(rtl_dir, f"{dut}.v"),
    ]

    parameters = {}

    parameters['LFSR_WIDTH'] = lfsr_width
    parameters['LFSR_POLY'] = lfsr_poly
    parameters['LFSR_CONFIG'] = lfsr_config
    parameters['LFSR_FEED_FORWARD'] = 0
    parameters['REVERSE'] = reverse
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
