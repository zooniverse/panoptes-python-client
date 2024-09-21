import ast


class CaesarRuleGenerator:
    def __init__(self, rule):
        self.tree = ast.parse(rule)

    def __call__(self, reducer_names):
        visitor = CaesarRuleGenParser(reducer_names=reducer_names)
        try:
            visitor.visit(self.tree)
        except ValueError as e:
            print("Error!", e)
            return
        return visitor.report()[0]


class CaesarRuleGenParser(ast.NodeVisitor):
    def __init__(self, reducer_names=None):
        super().__init__()
        self.rule_components = []
        self.sub_expr_level = 0
        self.reducers = reducer_names

    def binop_impl(self, node):
        # left, op, right
        return [self.visit(node.op), self.visit(node.left), self.visit(node.right)]

    def visit_BinOp(self, node):
        if not self.sub_expr_level:
            # only append top level operations
            self.sub_expr_level += 1
            self.rule_components.append(self.binop_impl(node))
            self.sub_expr_level -= 1
        else:
            return self.binop_impl(node)

    def compare_impl(self, node):
        # left, ops, comparators
        if len(node.ops) > 1:
            op = node.ops.pop(0)
            left = node.left
            node.left = node.comparators.pop(0)
            return [self.visit(op), self.visit(left)] + [self.visit(node)]
        return [
            self.visit(node.ops[0]),
            self.visit(node.left),
            self.visit(node.comparators[0]),
        ]

    def visit_Compare(self, node):
        if not self.sub_expr_level:
            # only append top level operations
            self.sub_expr_level += 1
            self.rule_components.append(self.compare_impl(node))
            self.sub_expr_level -= 1
        else:
            return self.compare_impl(node)

    def boolop_impl(self, node):
        # op, values
        return [self.visit(node.op)] + [self.visit(value) for value in node.values]

    def visit_BoolOp(self, node):
        if not self.sub_expr_level:
            # only append top level operations
            self.sub_expr_level += 1
            self.rule_components.append(self.boolop_impl(node))
            self.sub_expr_level -= 1
        return self.boolop_impl(node)

    def bad_name_error(self):
        return (
            "Lookup names must start with 'subject'"
            + " or the name of a registered reducer.\n"
            + " Registered reducers are:\n"
            + "\n".join(self.reducers)
        )

    def visit_Subscript(self, node):
        # Lookups without a default
        lookup_category = node.value.id
        lookup_attribute = node.slice.value
        if lookup_category == "subject":
            return ["lookup", f"{lookup_category}.{lookup_attribute}"]
        if self.reducers is None or lookup_category not in self.reducers:
            raise ValueError(self.bad_name_error())
        return ["lookup", f"{lookup_category}.{lookup_attribute}"]

    def bad_lookup_def_error(self):
        return "Bad lookup definition."

    def visit_List(self, node):
        # Lookups with a default
        criterion = (
            len(node.elts) == 2
            and type(node.elts[0]) == ast.Subscript
            and type(node.elts[1]) == ast.Constant
        )
        if not criterion:
            raise ValueError(self.bad_lookup_def_error())

        lookup = self.visit(node.elts[0]) + [self.visit(node.elts[1])]
        return lookup

    def const_type_handler(self, value):
        if type(value) == bool:
            return "true" if value else "false"
        return value

    def visit_Constant(self, node):
        # value, kind
        return ["const", self.const_type_handler(node.value)]

    def visit_Add(self, node):
        return "+"

    def visit_Sub(self, node):
        return "-"

    def visit_Mult(self, node):
        return "*"

    def visit_Div(self, node):
        return "/"

    def visit_And(self, node):
        return "and"

    def visit_Or(self, node):
        return "or"

    def visit_Eq(self, node):
        return "eq"

    def visit_GtE(self, node):
        return "gte"

    def visit_LtE(self, node):
        return "lte"

    def visit_Gt(self, node):
        return "gt"

    def visit_Lt(self, node):
        return "lt"

    def report(self):
        return self.rule_components
