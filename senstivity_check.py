# sensitivity_checker.py

from ast import stmt
import sys
from pyverilog.vparser.ast import Always, Sens, Identifier
from collections import defaultdict

def collect_read_ids(node, reads):
    """
    Recursively walk the AST 'node' and collect all Identifier names
    that appear in expressions/statements (except on the left of assignments).
    """
    for c in getattr(node, 'children', lambda: [])():
        if isinstance(c, Identifier):
            reads.add(c.name)
        else:
            collect_read_ids(c, reads)

def check_sensitivity(ast, module_name):
    """
    Scan all Always nodes in the AST, and for each one that
    uses an explicit sensitivity list (not '*'),
    compare the list of sens_list entries to the actual read signals.
    """
    warnings = []
    for item in ast.description.definitions:
        # Only check the target module
        if any(getattr(s.sig, 'name', None) == '*' for s in stmt.sens_list.list):
         continue
        for stmt in getattr(item, 'items', []):
            if not isinstance(stmt, Always):
                continue
            # skip wildcard @*
            if stmt.sens_list.type == 'star':
                continue
            # collect sensitivity list names
            sens_names = set()
            for s in stmt.sens_list.list:
                if isinstance(s, Sens) and isinstance(s.sig, Identifier):
                    sens_names.add(s.sig.name)
            # collect read identifiers in body
            read_names = set()
            collect_read_ids(stmt.statement, read_names)
            # any reads not in sensitivity?
            missing = read_names - sens_names
            if missing:
                warnings.append(
                    (item.name,
                     stmt.sens_list,
                     missing))
    return warnings

def report_warnings(warnings):
    """
    Print warnings in human‑readable form.
    """
    for mod, sens_list, missing in warnings:
        sens_str = ", ".join(s.sig.name for s in sens_list.list if isinstance(s, Sens))
        miss_str = ", ".join(sorted(missing))
        print(f"[WARN] Module '{mod}': always @({sens_str}) missing signals: {miss_str}")
