# Copyright (c) 2023 Alex Forencich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

TOPLEVEL_LANG = verilog

SIM ?= icarus
WAVES ?= 0

COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

DUT      = lfsr_crc
TOPLEVEL = $(DUT)
MODULE   = test_$(DUT)
VERILOG_SOURCES += ../../rtl/$(DUT).v
VERILOG_SOURCES += ../../rtl/lfsr.v

# module parameters
export PARAM_LFSR_WIDTH ?= 32
export PARAM_LFSR_POLY ?= "32'h4c11db7"
export PARAM_LFSR_INIT ?= "32'hffffffff"
export PARAM_LFSR_CONFIG ?= "\"GALOIS\""
export PARAM_REVERSE ?= 1
export PARAM_INVERT ?= 1
export PARAM_DATA_WIDTH ?= 8
export PARAM_STYLE ?= "\"AUTO\""

ifeq ($(SIM), icarus)
	PLUSARGS += -fst

	COMPILE_ARGS += -P $(TOPLEVEL).LFSR_WIDTH=$(PARAM_LFSR_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).LFSR_POLY=$(PARAM_LFSR_POLY)
	COMPILE_ARGS += -P $(TOPLEVEL).LFSR_INIT=$(PARAM_LFSR_INIT)
	COMPILE_ARGS += -P $(TOPLEVEL).LFSR_CONFIG=$(PARAM_LFSR_CONFIG)
	COMPILE_ARGS += -P $(TOPLEVEL).REVERSE=$(PARAM_REVERSE)
	COMPILE_ARGS += -P $(TOPLEVEL).INVERT=$(PARAM_INVERT)
	COMPILE_ARGS += -P $(TOPLEVEL).DATA_WIDTH=$(PARAM_DATA_WIDTH)
	COMPILE_ARGS += -P $(TOPLEVEL).STYLE=$(PARAM_STYLE)

	ifeq ($(WAVES), 1)
		VERILOG_SOURCES += iverilog_dump.v
		COMPILE_ARGS += -s iverilog_dump
	endif
else ifeq ($(SIM), verilator)
	COMPILE_ARGS += -Wno-SELRANGE -Wno-WIDTH

	COMPILE_ARGS += -GLFSR_WIDTH=$(PARAM_LFSR_WIDTH)
	COMPILE_ARGS += -GLFSR_POLY=$(PARAM_LFSR_POLY)
	COMPILE_ARGS += -GLFSR_INIT=$(PARAM_LFSR_INIT)
	COMPILE_ARGS += -GLFSR_CONFIG=$(PARAM_LFSR_CONFIG)
	COMPILE_ARGS += -GREVERSE=$(PARAM_REVERSE)
	COMPILE_ARGS += -GINVERT=$(PARAM_INVERT)
	COMPILE_ARGS += -GDATA_WIDTH=$(PARAM_DATA_WIDTH)
	COMPILE_ARGS += -GSTYLE=$(PARAM_STYLE)

	ifeq ($(WAVES), 1)
		COMPILE_ARGS += --trace-fst
	endif
endif

include $(shell cocotb-config --makefiles)/Makefile.sim

iverilog_dump.v:
	echo 'module iverilog_dump();' > $@
	echo 'initial begin' >> $@
	echo '    $$dumpfile("$(TOPLEVEL).fst");' >> $@
	echo '    $$dumpvars(0, $(TOPLEVEL));' >> $@
	echo 'end' >> $@
	echo 'endmodule' >> $@

clean::
	@rm -rf iverilog_dump.v
	@rm -rf dump.fst $(TOPLEVEL).fst
