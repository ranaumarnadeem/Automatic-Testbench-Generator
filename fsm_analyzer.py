#!/usr/bin/env python3
"""
fsm_analyzer.py: Detect FSMs in a Verilog file using Pyverilog AST.
Usage: python3 fsm_analyzer.py design.v
"""

import sys
from pyverilog.vparser.parser import parse, ParseError
from pyverilog.vparser.ast import ModuleDef, Always, CaseStatement, Identifier

def parse_verilog(filename):
    print(f"[FSM] Parsing file: {filename}")
    try:
        ast, _ = parse([filename])
        print("[FSM] Parse successful.")
        return ast
    except ParseError as e:
        print(f"[FSM][ERROR] ParseError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[FSM][ERROR] Unexpected error: {e}")
        sys.exit(1)

def find_modules(ast):
    return [d for d in ast.description.definitions if isinstance(d, ModuleDef)]

def analyze_fsm(module):
    print(f"[FSM] Analyzing module '{module.name}'")
    transitions = {}
    try:
        for item in module.items:
            if isinstance(item, Always):
                cond = item.sens_list
                # look for CaseStatement inside
                for stmt in item.statement.statements or []:
                    if isinstance(stmt, CaseStatement):
                        var = stmt.comp  # Identifier of state signal
                        state_name = var.name if isinstance(var, Identifier) else str(var)
                        transitions[state_name] = []
                        for case in stmt.caselist:
                            case_val = case.value.value
                            for inner in case.statement.statements:
                                # look for non-blocking assigns to detect next-state
                                if hasattr(inner, 'right') and hasattr(inner, 'left'):
                                    ns = inner.left.var.name
                                    transitions[state_name].append((case_val, ns))
        print(f"[FSM] Found transitions: {transitions}")
    except Exception as e:
        print(f"[FSM][ERROR] Exception in analyze_fsm: {e}")
    return transitions

def main():
    if len(sys.argv) != 2:
        print("[FSM][ERROR] Usage: python3 fsm_analyzer.py <verilog_file>")
        sys.exit(1)

    filename = sys.argv[1]
    ast = parse_verilog(filename)
    modules = find_modules(ast)

    for m in modules:
        fsm = analyze_fsm(m)
        if fsm:
            print(f"[FSM] Module '{m.name}' transition table:")
            for state, trans in fsm.items():
                for val, nxt in trans:
                    print(f"    {state} --({val})-> {nxt}")
        else:
            print(f"[FSM] No FSM found in '{m.name}'")

if __name__ == "__main__":
    main()
