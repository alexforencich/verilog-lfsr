# Verilog LFSR Readme

For more information and updates: http://alexforencich.com/wiki/en/verilog/lfsr/start

GitHub repository: https://github.com/alexforencich/verilog-lfsr

## Introduction

Fully parametrizable combinatorial parallel LFSR/CRC module.  Implements an
unrolled LFSR next state computation.  Includes full MyHDL testbench.

## Documentation

### lfsr module

Fully parametrizable combinatorial parallel LFSR/CRC module.  Implements an
unrolled LFSR next state computation.

### lfsr_crc module

Wrapper for lfsr module for standard CRC computation.

### lfsr_descramble module

Wrapper for lfsr module for self-synchronizing descrambler.

### lfsr_prbs_gen module

Wrapper for lfsr module for standard PRBS computation.

### lfsr_scramble module

Wrapper for lfsr module for self-synchronizing scrambler.

### Source Files

    lfsr.v             : Parametrizable combinatorial LFSR/CRC module
    lfsr_crc.v         : Parametrizable CRC computation wrapper
    lfsr_descramble.v  : Parametrizable LFSR self-synchronizing descrambler
    lfsr_prbs_gen.v    : Parametrizable PRBS generator wrapper
    lfsr_scramble.v    : Parametrizable LFSR self-synchronizing scrambler

## Testing

Running the included testbenches requires MyHDL and Icarus Verilog.  Make sure
that myhdl.vpi is installed properly for cosimulation to work correctly.  The
testbenches can be run with a Python test runner like nose or py.test, or the
individual test scripts can be run with python directly.
