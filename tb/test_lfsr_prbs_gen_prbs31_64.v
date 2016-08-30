/*

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

*/

// Language: Verilog 2001

`timescale 1ns / 1ps

/*
 * Testbench for lfsr_prbs_gen
 */
module test_lfsr_prbs_gen_prbs31_64;

// Parameters
parameter LFSR_WIDTH = 31;
parameter LFSR_POLY = 31'h10000001;
parameter LFSR_INIT = {LFSR_WIDTH{1'b1}};
parameter LFSR_CONFIG = "FIBONACCI";
parameter REVERSE = 0;
parameter OUTPUT_WIDTH = 64;
parameter STYLE = "AUTO";

// Inputs
reg clk = 0;
reg rst = 0;
reg [7:0] current_test = 0;

reg enable = 0;

// Outputs
wire [OUTPUT_WIDTH-1:0] data_out;

initial begin
    // myhdl integration
    $from_myhdl(clk,
                rst,
                current_test,
                enable);
    $to_myhdl(data_out);

    // dump file
    $dumpfile("test_lfsr_prbs_gen_prbs31_64.lxt");
    $dumpvars(0, test_lfsr_prbs_gen_prbs31_64);
end

lfsr_prbs_gen #(
    .LFSR_WIDTH(LFSR_WIDTH),
    .LFSR_POLY(LFSR_POLY),
    .LFSR_INIT(LFSR_INIT),
    .LFSR_CONFIG(LFSR_CONFIG),
    .REVERSE(REVERSE),
    .OUTPUT_WIDTH(OUTPUT_WIDTH),
    .STYLE(STYLE)
)
UUT (
    .clk(clk),
    .rst(rst),
    .enable(enable),
    .data_out(data_out)
);

endmodule
