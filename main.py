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


def extract_ports(module, params):
    inputs = []
    outputs = []
    for port in module.portlist.ports:
        decl = port.first
        name = decl.name
        width_str, bit_width = resolve_width(decl.width, params)
        is_signed = getattr(decl, 'signed', False)
        entry = (name, width_str, bit_width, is_signed)
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

def generate_testbench(module_name, inputs, outputs):
    tb = []
    clk = next((n for n,_,_,_ in inputs if 'clk' in n.lower()), None)
    rst = next((n for n,_,_,_ in inputs if 'rst' in n.lower()), None)

    # Header & declarations
    tb.append("`timescale 1ns/1ps")
    tb.append(f"module {module_name}_tb;")
    for name, wstr, bw, signed in inputs:
        if name in (clk, rst):
            tb.append(f"    reg {name};")
        else:
            decl = f"reg {wstr} {name};".replace("  ", " ")
            tb.append(f"    {decl}")
    for name, wstr, bw, signed in outputs:
        decl = f"wire {wstr} {name};".replace("  ", " ")
        tb.append(f"    {decl}")
    tb.append("")

    # DUT instantiation
    tb.append(f"    {module_name} uut (")
    conns = [f"        .{n}({n})" for n,_,_,_ in inputs + outputs]
    for i, line in enumerate(conns):
        comma = "," if i < len(conns)-1 else ""
        tb.append(line + comma)
    tb.append("    );\n")

    # Clock & reset
    if clk:
        tb += [
            "    // Clock generation",
            f"    initial {clk} = 0;",
            f"    always #5 {clk} = ~{clk};\n"
        ]
    if rst:
        tb += [
            "    // Reset sequence",
            "    initial begin",
            f"        {rst} = 1; #10; {rst} = 0;",
            "    end\n"
        ]

    # Stimulus
    tb.append("    // Input stimulus")
    tb.append("    initial begin")
    for name,_,_,_ in inputs:
        if name not in (clk, rst):
            tb.append(f"        {name} = 0;")
    tb.append("        #10;")

    # Build test_ports list
    test_ports = [(n, bw, signed) for (n,_,bw,signed) in inputs if n not in (clk, rst)]
    total_bits = sum(bw for _,bw,_ in test_ports)

    # Exhaustive vs random
    if total_bits <= 12:
        # Exhaustive signed‑aware ranges
        ranges = []
        names  = []
        for n, bw, signed in test_ports:
            names.append(n)
            if signed:
                lo = -(2**(bw-1))
                hi =  2**(bw-1) - 1
            else:
                lo, hi = 0, 2**bw - 1
            ranges.append(range(lo, hi+1))
        for combo in product(*ranges):
            for n,v in zip(names, combo):
                tb.append(f"        {n} = {v};")
            tb.append("        #10;")
    else:
        # Warn if any signed port is present
        if any(signed for _,_,signed in test_ports):
            tb.append(f"        // [WARN] Signed ports present: random stimulus will omit negative values")
        tb.append("        // Too many combinations; random sampling")
        tb.append("        repeat (16) begin")
        for n, bw, signed in test_ports:
            if signed:
                tb.append(f"            {n} = $random % (1<<{bw}); // only non‑negative")
            else:
                tb.append(f"            {n} = $random % (1<<{bw});")
        tb.append("            #10;")
        tb.append("        end")

    tb += [
        "        $finish;",
        "    end",
        "endmodule"
    ]
    return "\n".join(tb)


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