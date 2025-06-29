#!/usr/bin/env python3
"""
main.py: Automatically generate a Verilog testbench for a given module using Pyverilog.
Usage: python3 main.py design.v
The generated testbench is appended to the end of design.v.
"""
import sys
from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import ModuleDef, Ioport, Input, Output, Width, IntConst
import itertools

def parse_verilog(filename):
    """Parse the Verilog file and return the AST."""
    ast, _ = parse([filename])
    return ast

def find_top_module(ast):
    """Find the top module (we take the last ModuleDef in the file)."""
    modules = [item for item in ast.description.definitions if isinstance(item, ModuleDef)]
    if not modules:
        return None
    return modules[-1]  # assume last module is top

def extract_ports(module):
    """Extract (name, width) of input and output ports from the ModuleDef."""
    inputs = []
    outputs = []
    for item in module.portlist.ports:
        decl = item.first
        name = decl.name
        width_str = ""
        bit_width = 1
        if hasattr(decl, 'width') and decl.width is not None:
            try:
                msb = int(decl.width.msb.value)
                lsb = int(decl.width.lsb.value)
                bit_width = abs(msb - lsb) + 1
                width_str = f"[{msb}:{lsb}]"
            except:
                bit_width = 1
                width_str = ""
        if isinstance(decl, Input):
            inputs.append((name, width_str, bit_width))
        elif isinstance(decl, Output):
            outputs.append((name, width_str, bit_width))
    return inputs, outputs

def generate_all_combinations(input_ports):
    """Generate all possible combinations of input values based on their widths (up to 4 bits total for safety)."""
    signal_ranges = []
    names = []
    total_bits = 0
    for name, _, width in input_ports:
        total_bits += width
        if total_bits > 12:  # Avoid explosion
            return None
        names.append(name)
        signal_ranges.append(range(2 ** width))
    return names, list(itertools.product(*signal_ranges))

def generate_testbench(module_name, inputs, outputs):
    tb_name = f"{module_name}_tb"
    lines = []
    lines.append(f"`timescale 1ns/1ps")
    lines.append(f"module {tb_name};")
    lines.append("    // Declare regs for inputs and wires for outputs")

    clk_name = next((n for n,_,_ in inputs if 'clk' in n.lower()), None)
    rst_name = next((n for n,_,_ in inputs if 'rst' in n.lower()), None)

    if clk_name:
        lines.append(f"    reg {clk_name};")
    if rst_name:
        lines.append(f"    reg {rst_name};")

    for name, width, _ in inputs:
        if name in [clk_name, rst_name]:
            continue
        lines.append(f"    reg {width} {name};".replace("  ", " "))

    for name, width, _ in outputs:
        lines.append(f"    wire {width} {name};".replace("  ", " "))

    lines.append("")
    lines.append(f"    // Instantiate the DUT")
    lines.append(f"    {module_name} uut (")
    port_conns = [f"        .{name}({name})" for name, _, _ in inputs + outputs]
    for i, conn in enumerate(port_conns):
        lines.append(conn + ("," if i < len(port_conns) - 1 else ""))
    lines.append(f"    );")

    if clk_name:
        lines.append("")
        lines.append(f"    // Clock generation")
        lines.append(f"    initial {clk_name} = 0;")
        lines.append(f"    always #5 {clk_name} = ~{clk_name};")

    if rst_name:
        lines.append("")
        lines.append(f"    // Reset sequence")
        lines.append(f"    initial begin")
        lines.append(f"        {rst_name} = 1;")
        lines.append(f"        #10;")
        lines.append(f"        {rst_name} = 0;")
        lines.append(f"    end")

    lines.append("")
    lines.append(f"    // Input stimulus")
    lines.append(f"    initial begin")
    for name, _, _ in inputs:
        if name not in [clk_name, rst_name]:
            lines.append(f"        {name} = 0;")
    lines.append("        #10;")

    comb = generate_all_combinations(inputs if not clk_name else [x for x in inputs if x[0] != clk_name])
    if comb is None:
        lines.append("        // Too many combinations, using limited random vectors")
        lines.append("        repeat (16) begin")
        for name, _, width in inputs:
            if name in [clk_name, rst_name]: continue
            lines.append(f"            {name} = $random % (1 << {width});")
        lines.append("            #10;")
        lines.append("        end")
    else:
        names, combos = comb
        for values in combos:
            for name, value in zip(names, values):
                lines.append(f"        {name} = {value};")
            lines.append("        #10;")

    lines.append("        $finish;")
    lines.append("    end")
    lines.append(f"endmodule")
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
