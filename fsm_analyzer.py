from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import Always, CaseStatement, Case, Identifier, BlockingSubstitution, IfStatement


def extract_fsms(ast):
    """
    Extract FSM-like structures from Verilog AST.
    Looks for 'always' blocks with 'case (state)' style patterns.
    Returns a list of FSMs with state transitions.
    """
    fsms = []
    definitions = ast.description.definitions

    for module in definitions:
        for item in module.items:
            if isinstance(item, Always):
                fsm_info = parse_always_block(item)
                if fsm_info:
                    fsms.append(fsm_info)

    return fsms


def parse_always_block(always_node):
    """
    Attempt to parse an always block to find FSM patterns.
    Look for case statements over a 'state' variable.
    """
    senslist = always_node.sens_list
    statement = always_node.statement

    if isinstance(statement, CaseStatement):
        return parse_case_fsm(statement)

    # Handle nested blocks like: always @(*) begin ... case(state) ... end
    elif hasattr(statement, 'statements'):
        for stmt in statement.statements:
            if isinstance(stmt, CaseStatement):
                return parse_case_fsm(stmt)
    return None


def parse_case_fsm(case_stmt):
    """
    Extract FSM info from case statement.
    """
    fsm = {
        'state_var': '',
        'states': {},  # key: state name, value: list of transitions
    }

    if isinstance(case_stmt.comp, Identifier):
        fsm['state_var'] = case_stmt.comp.name

    for case in case_stmt.caselist:
        if not case.exprs:
            continue
        state_expr = case.exprs[0]
        state_name = state_expr.value if hasattr(state_expr, 'value') else str(state_expr)
        transitions = []

        if hasattr(case.statement, 'statements'):
            for stmt in case.statement.statements:
                if isinstance(stmt, IfStatement):
                    cond = stmt.cond
                    body = stmt.then
                    target = extract_state_assignment(body)
                    if target:
                        transitions.append((cond, target))
                elif isinstance(stmt, BlockingSubstitution):
                    target = extract_state_assignment(stmt)
                    if target:
                        transitions.append(("1'b1", target))  # unconditional

        fsm['states'][state_name] = transitions

    return fsm


def extract_state_assignment(stmt):
    """
    Extract the target state from a BlockingSubstitution like: state = IDLE;
    """
    if isinstance(stmt, BlockingSubstitution):
        if isinstance(stmt.left, Identifier) and isinstance(stmt.right, Identifier):
            return stmt.right.name
    elif hasattr(stmt, 'statements'):
        for sub in stmt.statements:
            if isinstance(sub, BlockingSubstitution):
                return extract_state_assignment(sub)
    return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 fsm_analyzer.py design.v")
        sys.exit(1)

    ast, _ = parse([sys.argv[1]])
    fsms = extract_fsms(ast)

    if not fsms:
        print("No FSMs found.")
    else:
        for i, fsm in enumerate(fsms):
            print(f"FSM {i+1} with state variable: {fsm['state_var']}")
            for state, transitions in fsm['states'].items():
                print(f"  State {state}:")
                for cond, target in transitions:
                    cond_str = cond.to_verilog() if hasattr(cond, 'to_verilog') else str(cond)
                    print(f"    if ({cond_str}) -> {target}")
