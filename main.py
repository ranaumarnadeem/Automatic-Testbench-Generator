#!/usr/bin/env python3
"""
main.py: Automatically generate a Verilog testbench for a given module using Pyverilog.
Usage: python3 main.py design.v
The generated testbench is appended to the end of design.v.
"""
import sys
from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import ModuleDef, Ioport, Input, Output

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
        # Each item is an Ioport with first.child being Input or Output
        decl = item.first  # could be Input or Output node
        name = decl.name
        width = ""
        if hasattr(decl, 'width') and decl.width is not None:
            # width.msb and width.lsb are IntConst nodes
            try:
                msb = int(decl.width.msb.value)
                lsb = int(decl.width.lsb.value)
                width = f"[{msb}:{lsb}]"
            except:
                width = ""
        if isinstance(decl, Input):
            inputs.append((name, width))
        elif isinstance(decl, Output):
            outputs.append((name, width))
    return inputs, outputs

def generate_testbench(module_name, inputs, outputs):
    """Generate Verilog code for the testbench of one module."""
    tb_name = f"{module_name}_tb"
    lines = []
    lines.append(f"`timescale 1ns/1ps")
    lines.append(f"module {tb_name};")
    lines.append("    // Declare regs for inputs and wires for outputs")
    # Declare clk and rst if they appear in inputs
    clk_name = next((n for n,_ in inputs if 'clk' in n.lower()), None)
    rst_name = next((n for n,_ in inputs if 'rst' in n.lower()), None)
    if clk_name:
        lines.append(f"    reg {clk_name};")
    if rst_name:
        lines.append(f"    reg {rst_name};")
    # Declare other inputs
    for name, width in inputs:
        if name in [clk_name, rst_name]:
            continue
        decl = f"reg {width} {name};".replace("  ", " ")
        lines.append(f"    {decl}")
    # Declare outputs
    for name, width in outputs:
        decl = f"wire {width} {name};".replace("  ", " ")
        lines.append(f"    {decl}")
    lines.append("")
    # DUT instantiation
    lines.append(f"    // Instantiate the DUT")
    lines.append(f"    {module_name} uut (")
    # Connect ports by name
    port_conns = []
    for name, _ in inputs + outputs:
        port_conns.append(f"        .{name}({name})")
    # Join with commas, last one without comma
    for i, conn in enumerate(port_conns):
        if i < len(port_conns) - 1:
            lines.append(conn + ",")
        else:
            lines.append(conn)
    lines.append(f"    );")
    lines.append("")
    # Generate clock if needed
    if clk_name:
        lines.append(f"    // Clock generation")
        lines.append(f"    initial {clk_name} = 0;")
        lines.append(f"    always #5 {clk_name} = ~{clk_name};")
        lines.append("")
    # Apply reset if needed
    if rst_name:
        lines.append(f"    // Reset signal")
        lines.append(f"    initial begin")
        lines.append(f"        {rst_name} = 1;")
        lines.append(f"        #10;")
        lines.append(f"        {rst_name} = 0;")
        lines.append(f"    end")
        lines.append("")
    # Stimulus generation
    lines.append(f"    // Input stimulus")
    lines.append(f"    initial begin")
    # Initialize other inputs to 0
    for name, _ in inputs:
        if name in [clk_name, rst_name]:
            continue
        lines.append(f"        {name} = 0;")
    lines.append("        #10;")
    # Example: loop for random stimuli on inputs
    lines.append("        integer i;")
    lines.append("        for (i = 0; i < 16; i = i+1) begin")
    for name, _ in inputs:
        if name in [clk_name, rst_name]:
            continue
        # assign random; overflow bits are truncated
        lines.append(f"            {name} = $random;")
    lines.append("            #10;")
    lines.append("        end")
    lines.append("        $finish;")
    lines.append("    end")
    lines.append("")
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
    # Append testbench to file
    with open(filename, 'a') as f:
        f.write("\n\n// ---- Auto-generated testbench ----\n")
        f.write(tb_code)
    print(f"Testbench for module '{module_name}' appended to {filename}")

if __name__ == "__main__":
    main()
