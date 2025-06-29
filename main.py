#!/usr/bin/env python3
"""
main.py: Automatically generate a Verilog testbench for a given module using Pyverilog.
Usage: python3 main.py design.v
The generated testbench is appended to the end of design.v.
"""

import sys
import itertools
from pyverilog.vparser.parser import parse, ParseError
from pyverilog.vparser.ast import ModuleDef, Ioport, Input, Output

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
        return ""
    try:
        msb = eval(width_node.msb.value, {}, params)
        lsb = eval(width_node.lsb.value, {}, params)
        w = abs(msb - lsb) + 1
        print(f"[DEBUG] Resolved width [{msb}:{lsb}] → {w} bits")
        return w
    except Exception as e:
        print(f"[WARN] Could not resolve width node '{width_node}': {e}")
        return 1

def extract_ports(module, params):
    print(f"[DEBUG] Extracting ports from module '{module.name}'")
    inputs = []
    outputs = []
    try:
        for item in module.portlist.ports:
            decl = item.first
            name = decl.name
            width = resolve_width(decl.width, params)
            if isinstance(decl, Input):
                inputs.append((name, width))
                print(f"  [INPUT ] {name} : {width} bits")
            elif isinstance(decl, Output):
                outputs.append((name, width))
                print(f"  [OUTPUT] {name} : {width} bits")
    except Exception as e:
        print(f"[ERROR] Failed in extract_ports: {e}")
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
    print(f"[DEBUG] Generating testbench for '{module_name}'")
    try:
        clk = next((n for n, _ in inputs if 'clk' in n.lower()), None)
        rst = next((n for n, _ in inputs if 'rst' in n.lower()), None)

        lines = ["`timescale 1ns/1ps", f"module {module_name}_tb;"]

        # Declarations
        for name, width in inputs:
            decl = f"reg [{'{}:0'.format(width-1)}] {name};" if width>1 else f"reg {name};"
            lines.append("    " + decl)
        for name, width in outputs:
            decl = f"wire [{'{}:0'.format(width-1)}] {name};" if width>1 else f"wire {name};"
            lines.append("    " + decl)

        lines.append("")
        # Instantiation
        lines.append(f"    {module_name} uut (")
        conns = []
        for name, _ in inputs+outputs:
            conns.append(f"        .{name}({name})")
        lines.append(",\n".join(conns))
        lines.append("    );")

        # Clock/reset
        if clk:
            lines += ["", "    initial " + clk + " = 0;", f"    always #5 {clk} = ~{clk};"]
        if rst:
            lines += ["", "    initial begin", f"        {rst} = 1; #10; {rst} = 0;", "    end"]

        # Stimulus
        lines += ["", "    initial begin"]
        for name, _ in inputs:
            if name not in (clk, rst):
                lines.append(f"        {name} = 0;")
        lines.append("        #10;")

        names, combos = generate_all_combinations(inputs, clk)
        if combos is None:
            lines += ["        // fallback random stimulus", "        repeat(16) begin"]
            for name, width in inputs:
                if name in (clk, rst):
                    continue
                lines.append(f"            {name} = $random % {2**width};")
            lines += ["            #10;", "        end"]
        else:
            for combo in combos:
                for name, val in zip(names, combo):
                    lines.append(f"        {name} = {val};")
                lines.append("        #10;")

        lines += ["        $finish;", "    end", "endmodule"]
        tb = "\n".join(lines)
        print("[DEBUG] Testbench generation complete.")
        return tb
    except Exception as e:
        print(f"[ERROR] Exception in generate_testbench: {e}")
        return "// ERROR generating testbench"

def main():
    if len(sys.argv) != 2:
        print("[ERROR] Usage: python3 main.py <verilog_file>")
        sys.exit(1)

    filename = sys.argv[1]
    ast = parse_verilog(filename)
    top = find_top_module(ast)
    if not top:
        print("[ERROR] No top module found.")
        sys.exit(1)

    params = extract_parameters(top)
    inputs, outputs = extract_ports(top, params)
    tb = generate_testbench(top.name, inputs, outputs)

    try:
        with open(filename, 'a') as f:
            f.write("\n\n// ---- Auto-generated testbench ----\n")
            f.write(tb)
        print(f"[INFO] Testbench appended to {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to write testbench to file: {e}")

if __name__ == "__main__":
    main()
