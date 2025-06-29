#!/usr/bin/env python3
"""
main.py: Automatically generate an exhaustive Verilog testbench using Pyverilog.
Usage: python3 main.py design.v
The generated testbench is appended to the end of design.v.
"""

import sys
import itertools
from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import ModuleDef, Ioport, Input, Output

def parse_verilog(filename):
    ast, _ = parse([filename])
    return ast

def find_top_module(ast):
    modules = [item for item in ast.description.definitions if isinstance(item, ModuleDef)]
    if not modules:
        return None
    return modules[-1]

def extract_ports(module):
    inputs = []
    outputs = []
    for item in module.portlist.ports:
        decl = item.first
        name = decl.name
        width = 1
        if hasattr(decl, 'width') and decl.width is not None:
            try:
                msb = int(decl.width.msb.value)
                lsb = int(decl.width.lsb.value)
                width = abs(msb - lsb) + 1
            except:
                width = 1
        if isinstance(decl, Input):
            inputs.append((name, width))
        elif isinstance(decl, Output):
            outputs.append((name, width))
    return inputs, outputs

def generate_stimulus(input_signals, clk_name=None, rst_name=None):
    filtered_inputs = [(name, width) for name, width in input_signals if name not in [clk_name, rst_name]]
    if not filtered_inputs:
        return "// No testable inputs for stimulus generation."

    ranges = [range(2 ** width) for _, width in filtered_inputs]
    combos = list(itertools.product(*ranges))

    lines = []
    for combo in combos:
        line = "        #10 " + "; ".join(f"{name} = {val}" for (name, _), val in zip(filtered_inputs, combo)) + ";"
        lines.append(line)
    lines.append("        $finish;")
    return "\n".join(lines)

def generate_testbench(module_name, inputs, outputs):
    tb_name = f"{module_name}_tb"
    lines = [f"`timescale 1ns/1ps", f"module {tb_name};", "// Declare inputs and outputs"]

    clk_name = next((n for n, _ in inputs if 'clk' in n.lower()), None)
    rst_name = next((n for n, _ in inputs if 'rst' in n.lower()), None)

    for name, width in inputs:
        lines.append(f"    reg [{width-1}:0] {name};" if width > 1 else f"    reg {name};")
    for name, width in outputs:
        lines.append(f"    wire [{width-1}:0] {name};" if width > 1 else f"    wire {name};")
    lines.append("")

    lines.append("// Instantiate DUT")
    lines.append(f"    {module_name} uut (")
    port_lines = [f"        .{name}({name})" for name, _ in inputs + outputs]
    lines.append(",\n".join(port_lines))
    lines.append("    );\n")

    if clk_name:
        lines.append("// Clock generation")
        lines.append(f"    initial {clk_name} = 0;")
        lines.append(f"    always #5 {clk_name} = ~{clk_name};\n")

    lines.append("initial begin")
    if rst_name:
        lines.append(f"    {rst_name} = 1; #10; {rst_name} = 0;")

    stimulus = generate_stimulus(inputs, clk_name, rst_name)
    lines.append(stimulus)
    lines.append("end\nendmodule")
    return "\n".join(lines)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <verilog_file>")
        sys.exit(1)

    filename = sys.argv[1]
    ast = parse_verilog(filename)
    top_module = find_top_module(ast)
    if top_module is None:
        print("No module found in the file.")
        sys.exit(1)

    module_name = top_module.name
    inputs, outputs = extract_ports(top_module)
    tb_code = generate_testbench(module_name, inputs, outputs)

    with open(filename, 'a') as f:
        f.write("\n\n// ---- Auto-generated testbench ----\n")
        f.write(tb_code)
    print(f"Testbench for module '{module_name}' appended to {filename}")

if __name__ == "__main__":
    main()
