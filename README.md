# Verilog LFSR Readme

[![Build Status](https://github.com/alexforencich/verilog-lfsr/workflows/Regression%20Tests/badge.svg?branch=master)](https://github.com/alexforencich/verilog-lfsr/actions/)

For more information and updates: http://alexforencich.com/wiki/en/verilog/lfsr/start

GitHub repository: https://github.com/alexforencich/verilog-lfsr

## Deprecation Notice

This repository is superseded by https://github.com/fpganinja/taxi.  All new features and bug fixes will be applied there, and commercial support is also available.  As a result, this repo is deprecated and will not receive any future maintenance or support.

## Introduction

Fully parametrizable combinatorial parallel LFSR/CRC module.  Implements an unrolled LFSR next state computation.  Includes full cocotb testbenches.

## Documentation

### lfsr module

Fully parametrizable combinatorial parallel LFSR/CRC module.  Implements an unrolled LFSR next state computation.

### lfsr_crc module

Wrapper for lfsr module for standard CRC computation.

### lfsr_descramble module

Wrapper for lfsr module for self-synchronizing descrambler.

### lfsr_prbs_check module

Wrapper for lfsr module for standard PRBS check.

### lfsr_prbs_gen module

Wrapper for lfsr module for standard PRBS computation.

### lfsr_scramble module

Wrapper for lfsr module for self-synchronizing scrambler.

### Source Files

    lfsr.v             : Parametrizable combinatorial LFSR/CRC module
    lfsr_crc.v         : Parametrizable CRC computation wrapper
    lfsr_descramble.v  : Parametrizable LFSR self-synchronizing descrambler
    lfsr_prbs_check.v  : Parametrizable PRBS checker wrapper
    lfsr_prbs_gen.v    : Parametrizable PRBS generator wrapper
    lfsr_scramble.v    : Parametrizable LFSR self-synchronizing scrambler

## Testing

Running the included testbenches requires [cocotb](https://github.com/cocotb/cocotb) and [Icarus Verilog](http://iverilog.icarus.com/).  The testbenches can be run with pytest directly (requires [cocotb-test](https://github.com/themperek/cocotb-test)), pytest via tox, or via cocotb makefiles.
