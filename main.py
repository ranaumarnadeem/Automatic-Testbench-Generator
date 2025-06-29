#!/usr/bin/env python3
"""
main.py: Automatically generate a Verilog testbench for a given module using Pyverilog.
Usage: python3 main.py design.v
The generated testbench is appended to the end of design.v.
"""
import itertools

import sys
from itertools import product

from pyverilog.vparser.parser import parse, ParseError
from pyverilog.vparser.ast import ModuleDef, Ioport, Input, Output
from senstivity_check import check_sensitivity, report_warnings

def parse_verilog(filename):
    print(f"[DEBUG] Parsing Verilog file: {filename}")
    try:
        ast, _ = parse([filename])
        print("[DEBUG] Parsing succeeded.")
        return ast
    except ParseError as e:
        print(f"[ERROR] Failed to parse {filename}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error during parse: {e}")
        sys.exit(1)

def find_top_module(ast):
    print("[DEBUG] Locating top module...")
    try:
        modules = [d for d in ast.description.definitions if isinstance(d, ModuleDef)]
        if not modules:
            print("[ERROR] No ModuleDef found in AST.")
            return None
        top = modules[-1]
        print(f"[DEBUG] Top module is '{top.name}'.")
        return top
    except Exception as e:
        print(f"[ERROR] Exception in find_top_module: {e}")
        return None

def extract_parameters(module):
    print(f"[DEBUG] Extracting parameters from module '{module.name}'")
    params = {}
    try:
        for param in getattr(module, 'paramlist', {}).params or []:
            params[param.name] = int(param.value.value)
            print(f"  [PARAM] {param.name} = {params[param.name]}")
    except Exception as e:
        print(f"[ERROR] Failed to extract parameters: {e}")
    return params

def resolve_width(width_node, params):
    if width_node is None:
        return "", 1
    try:
        msb = eval(width_node.msb.value, {}, params)
        lsb = eval(width_node.lsb.value, {}, params)
        bw = abs(msb - lsb) + 1
        return f"[{msb}:{lsb}]", bw
    except Exception:
        return "", 1

def extract_ports(module, param_dict):
    """Extract input and output ports, handling widths and array dimensions."""
    def resolve_width(width_node):
        if width_node is None:
            return 1
        try:
            msb = eval(width_node.msb.value, {}, param_dict)
            lsb = eval(width_node.lsb.value, {}, param_dict)
            return abs(msb - lsb) + 1
        except Exception:
            return 1

    inputs = []
    outputs = []

    for port in module.portlist.ports:
        decl = port.first
        name = decl.name

        # Handle vector width
        width = resolve_width(decl.width)

        # Handle unpacked array size
        array_size = 1
        is_array = False
        if hasattr(decl, 'dimensions') and decl.dimensions:
            try:
                dim = decl.dimensions[0]
                msb = eval(dim.msb.value, {}, param_dict)
                lsb = eval(dim.lsb.value, {}, param_dict)
                array_size = abs(msb - lsb) + 1
                is_array = True
            except Exception:
                pass

        entry = (name, width, is_array, array_size)

        if isinstance(decl, Input):
            inputs.append(entry)
        elif isinstance(decl, Output):
            outputs.append(entry)

    return inputs, outputs



def generate_all_combinations(inputs, clk_name):
    print("[DEBUG] Generating exhaustive combinations...")
    names = []
    ranges = []
    total_bits = 0
    for name, width in inputs:
        if name == clk_name:
            continue
        total_bits += width
        if total_bits > 12:
            print("[WARN] Total bit-width exceeds 12, skipping exhaustive combos.")
            return None, None
        names.append(name)
        ranges.append(range(2**width))
    combos = list(itertools.product(*ranges))
    print(f"[DEBUG] Generated {len(combos)} combinations.")
    return names, combos

def generate_testbench(module_name, inputs, outputs, parameters=None):
    tb_name = f"{module_name}_tb"
    lines = []
    lines.append("`timescale 1ns/1ps")
    lines.append(f"module {tb_name};")
    lines.append("    // Declare regs for inputs and wires for outputs")

    clk_name = next((n for n, _, _, _ in inputs if 'clk' in n.lower()), None)
    rst_name = next((n for n, _, _, _ in inputs if 'rst' in n.lower()), None)

    # Declare inputs
    for name, width, is_array, dim in inputs:
        decl = "reg"
        if width > 1:
            decl += f" [{width-1}:0]"
        if is_array:
            decl += f" {name} [0:{dim-1}];"
        else:
            decl += f" {name};"
        lines.append(f"    {decl}")

    # Declare outputs
    for name, width, is_array, dim in outputs:
        decl = "wire"
        if width > 1:
            decl += f" [{width-1}:0]"
        if is_array:
            decl += f" {name} [0:{dim-1}];"
        else:
            decl += f" {name};"
        lines.append(f"    {decl}")

    lines.append("")
    lines.append("    // Instantiate the DUT")
    if parameters:
        param_strs = [f".{pname}({pval})" for pname, pval in parameters.items()]
        lines.append(f"    {module_name} #(")
        for i, p in enumerate(param_strs):
            lines.append(f"        {p}{',' if i < len(param_strs)-1 else ''}")
        lines.append(f"    ) uut (")
    else:
        lines.append(f"    {module_name} uut (")

    # Connections
    port_conns = []
    for name, _, _, _ in inputs + outputs:
        port_conns.append(f"        .{name}({name})")
    for i, conn in enumerate(port_conns):
        lines.append(conn + ("," if i < len(port_conns) - 1 else ""))
    lines.append(f"    );\n")

    # Clock gen
    if clk_name:
        lines.append("    // Clock generation")
        lines.append(f"    initial {clk_name} = 0;")
        lines.append(f"    always #5 {clk_name} = ~{clk_name};")
        lines.append("")

    # Reset logic
    if rst_name:
        lines.append("    // Reset sequence")
        lines.append(f"    initial begin")
        lines.append(f"        {rst_name} = 1;")
        lines.append(f"        #10;")
        lines.append(f"        {rst_name} = 0;")
        lines.append(f"    end\n")

    # Stimulus
    lines.append("    // Stimulus")
    lines.append("    initial begin")
    for name, width, is_array, dim in inputs:
        if name in [clk_name, rst_name]:
            continue
        if is_array:
            for i in range(dim):
                lines.append(f"        {name}[{i}] = 0;")
        else:
            lines.append(f"        {name} = 0;")
    lines.append("        #10;")

    # Stimulus loop
    lines.append("        // Example stimulus pattern")
    lines.append("        integer i;")
    lines.append("        for (i = 0; i < 4; i = i + 1) begin")
    for name, width, is_array, dim in inputs:
        if name in [clk_name, rst_name]:
            continue
        if is_array:
            for j in range(dim):
                val = f"(i + {j}) % {2**width}" if width else f"(i + {j})"
                lines.append(f"            {name}[{j}] = {val};")
        else:
            val = f"i % {2**width}" if width else "i"
            lines.append(f"            {name} = {val};")
    lines.append("            #10;")
    lines.append("        end")
    lines.append("        $finish;")
    lines.append("    end")
    lines.append("endmodule")

    return "\n".join(lines)

def main():
    if len(sys.argv) != 2:
        print("[ERROR] Usage: python3 main.py <verilog_file>")
        sys.exit(1)

    filename = sys.argv[1]

    # 1. Parse the Verilog file
    ast = parse_verilog(filename)

    # 2. Locate the top module
    top = find_top_module(ast)
    if not top:
        print("[ERROR] No top module found.")
        sys.exit(1)
    module_name = top.name
    print(f"[INFO] Top module: '{module_name}'")

    # 3. Sensitivity‑list completeness check
    try:
        warnings = check_sensitivity(ast, module_name)
        if warnings:
            print("[INFO] Sensitivity‑list checks:")
            report_warnings(warnings)
        else:
            print("[INFO] All explicit sensitivity lists are complete.")
    except Exception as e:
        print(f"[ERROR] Sensitivity check failed: {e}")

    # 4. Extract parameters
    params = extract_parameters(top)
    if params:
        print(f"[INFO] Parameters: {params}")

    # 5. Extract ports (with resolved widths)
    inputs, outputs = extract_ports(top, params)
    print(f"[DEBUG] Inputs:  {inputs}")
    print(f"[DEBUG] Outputs: {outputs}")

    # 6. Generate the testbench code
    tb_code = generate_testbench(module_name, inputs, outputs)
    if tb_code.startswith("// ERROR"):
        print("[ERROR] Testbench generation encountered an error. See above.")
        sys.exit(1)

    # 7. Append testbench to the source file
    try:
        with open(filename, 'a') as f:
            f.write("\n\n// ---- Auto-generated testbench ----\n")
            f.write(tb_code)
        print(f"[INFO] Testbench appended to '{filename}'.")
    except Exception as e:
        print(f"[ERROR] Failed to write testbench: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()