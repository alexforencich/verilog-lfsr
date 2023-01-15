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

`resetall
`timescale 1ns / 1ps
`default_nettype none

/*
 * LFSR CRC generator
 */
module lfsr_crc #
(
    // width of LFSR
    parameter LFSR_WIDTH = 32,
    // LFSR polynomial
    parameter LFSR_POLY = 32'h04c11db7,
    // Initial state
    parameter LFSR_INIT = {LFSR_WIDTH{1'b1}},
    // LFSR configuration: "GALOIS", "FIBONACCI"
    parameter LFSR_CONFIG = "GALOIS",
    // bit-reverse input and output
    parameter REVERSE = 1,
    // invert output
    parameter INVERT = 1,
    // width of data input and output
    parameter DATA_WIDTH = 8,
    // implementation style: "AUTO", "LOOP", "REDUCTION"
    parameter STYLE = "AUTO"
)
(
    input  wire                  clk,
    input  wire                  rst,
    input  wire [DATA_WIDTH-1:0] data_in,
    input  wire                  data_in_valid,
    output wire [LFSR_WIDTH-1:0] crc_out
);

/*

Fully parametrizable combinatorial parallel LFSR CRC module.  Implements an unrolled LFSR
next state computation.  

Ports:

clk

Clock input

rst

Reset module, set state to LFSR_INIT

data_in

CRC data input

data_in_valid

Shift input data through CRC when asserted

data_out

LFSR output (OUTPUT_WIDTH bits)

Parameters:

LFSR_WIDTH

Specify width of LFSR/CRC register

LFSR_POLY

Specify the LFSR/CRC polynomial in hex format.  For example, the polynomial

x^32 + x^26 + x^23 + x^22 + x^16 + x^12 + x^11 + x^10 + x^8 + x^7 + x^5 + x^4 + x^2 + x + 1

would be represented as

32'h04c11db7

Note that the largest term (x^32) is suppressed.  This term is generated automatically based
on LFSR_WIDTH.

LFSR_INIT

Initial state of LFSR.  Defaults to all 1s.

LFSR_CONFIG

Specify the LFSR configuration, either Fibonacci or Galois.  Fibonacci is generally used
for linear-feedback shift registers (LFSR) for pseudorandom binary sequence (PRBS) generators,
scramblers, and descrambers, while Galois is generally used for cyclic redundancy check
generators and checkers.

Fibonacci style (example for 64b66b scrambler, 0x8000000001)

   DIN (LSB first)
    |
    V
   (+)<---------------------------(+)<-----------------------------.
    |                              ^                               |
    |  .----.  .----.       .----. |  .----.       .----.  .----.  |
    +->|  0 |->|  1 |->...->| 38 |-+->| 39 |->...->| 56 |->| 57 |--'
    |  '----'  '----'       '----'    '----'       '----'  '----'
    V
   DOUT

Galois style (example for CRC16, 0x8005)

    ,-------------------+-------------------------+----------(+)<-- DIN (MSB first)
    |                   |                         |           ^
    |  .----.  .----.   V   .----.       .----.   V   .----.  |
    `->|  0 |->|  1 |->(+)->|  2 |->...->| 14 |->(+)->| 15 |--+---> DOUT
       '----'  '----'       '----'       '----'       '----'

REVERSE

Bit-reverse LFSR input and output.  Shifts MSB first by default, set REVERSE for LSB first.

INVERT

Bitwise invert CRC output.

DATA_WIDTH

Specify width of input data bus.  The module will perform one shift per input data bit,
so if the input data bus is not required tie data_in to zero and set DATA_WIDTH to the
required number of shifts per clock cycle.  

STYLE

Specify implementation style.  Can be "AUTO", "LOOP", or "REDUCTION".  When "AUTO"
is selected, implemenation will be "LOOP" or "REDUCTION" based on synthesis translate
directives.  "REDUCTION" and "LOOP" are functionally identical, however they simulate
and synthesize differently.  "REDUCTION" is implemented with a loop over a Verilog
reduction operator.  "LOOP" is implemented as a doubly-nested loop with no reduction
operator.  "REDUCTION" is very fast for simulation in iverilog and synthesizes well in
Quartus but synthesizes poorly in ISE, likely due to large inferred XOR gates causing
problems with the optimizer.  "LOOP" synthesizes will in both ISE and Quartus.  "AUTO"
will default to "REDUCTION" when simulating and "LOOP" for synthesizers that obey
synthesis translate directives.

Settings for common LFSR/CRC implementations:

Name        Configuration           Length  Polynomial      Initial value   Notes
CRC16-IBM   Galois, bit-reverse     16      16'h8005        16'hffff
CRC16-CCITT Galois                  16      16'h1021        16'h1d0f
CRC32       Galois, bit-reverse     32      32'h04c11db7    32'hffffffff    Ethernet FCS; invert final output
CRC32C      Galois, bit-reverse     32      32'h1edc6f41    32'hffffffff    iSCSI, Intel CRC32 instruction; invert final output

*/

reg [LFSR_WIDTH-1:0] state_reg = LFSR_INIT;
reg [LFSR_WIDTH-1:0] output_reg = 0;

wire [LFSR_WIDTH-1:0] lfsr_state;

assign crc_out = output_reg;

lfsr #(
    .LFSR_WIDTH(LFSR_WIDTH),
    .LFSR_POLY(LFSR_POLY),
    .LFSR_CONFIG(LFSR_CONFIG),
    .LFSR_FEED_FORWARD(0),
    .REVERSE(REVERSE),
    .DATA_WIDTH(DATA_WIDTH),
    .STYLE(STYLE)
)
lfsr_inst (
    .data_in(data_in),
    .state_in(state_reg),
    .data_out(),
    .state_out(lfsr_state)
);

always @(posedge clk) begin
    if (rst) begin
        state_reg <= LFSR_INIT;
        output_reg <= 0;
    end else begin
        if (data_in_valid) begin
            state_reg <= lfsr_state;
            if (INVERT) begin
                output_reg <= ~lfsr_state;
            end else begin
                output_reg <= lfsr_state;
            end
        end
    end
end

endmodule

`resetall
