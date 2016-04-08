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
 * Testbench for lfsr_crc
 */
module test_lfsr_crc_crc32;

// Parameters
parameter LFSR_WIDTH = 32;
parameter LFSR_POLY = 32'h04c11db7;
parameter LFSR_INIT = {LFSR_WIDTH{1'b1}};
parameter LFSR_CONFIG = "GALOIS";
parameter REVERSE = 1;
parameter INVERT = 1;
parameter DATA_WIDTH = 8;
parameter OUTPUT_WIDTH = LFSR_WIDTH;
parameter STYLE = "AUTO";

// Inputs
reg clk = 0;
reg rst = 0;
reg [7:0] current_test = 0;

reg [DATA_WIDTH-1:0] data_in = 0;
reg data_in_valid = 0;

// Outputs
wire [OUTPUT_WIDTH-1:0] crc_out;

initial begin
    // myhdl integration
    $from_myhdl(clk,
                rst,
                current_test,
                data_in,
                data_in_valid);
    $to_myhdl(crc_out);

    // dump file
    $dumpfile("test_lfsr_crc_crc32.lxt");
    $dumpvars(0, test_lfsr_crc_crc32);
end

lfsr_crc #(
    .LFSR_WIDTH(LFSR_WIDTH),
    .LFSR_POLY(LFSR_POLY),
    .LFSR_INIT(LFSR_INIT),
    .LFSR_CONFIG(LFSR_CONFIG),
    .REVERSE(REVERSE),
    .INVERT(INVERT),
    .DATA_WIDTH(DATA_WIDTH),
    .OUTPUT_WIDTH(OUTPUT_WIDTH),
    .STYLE(STYLE)
)
UUT (
    .clk(clk),
    .rst(rst),
    .data_in(data_in),
    .data_in_valid(data_in_valid),
    .crc_out(crc_out)
);

endmodule
