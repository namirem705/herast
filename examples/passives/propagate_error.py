from herapi import *

pattern = IfInsPat(
	VarBind("error_var"),
	ExInsPat(BindItem("logic_expr")),
	ExInsPat(AsgExprPat(VarBind("error_var"), BindItem("logic_expr")))
)

"""
This scheme replaces things like
	if (error_var) {
		logic_expr;
	} else {
		error_var = logic_expr;
	}
to
	error_var = __propagate_error(error_var, logic_expr);
"""
class ReplacingScheme(SPScheme):
	def on_matched_item(self, item, ctx: PatternContext):
		error_var = ctx.get_var("error_var")
		if error_var is None:
			return False

		logic_expr = ctx.get_expr("logic_expr")
		if logic_expr is None:
			return False

		new_item = make_call_helper_instr("__propagate_error", error_var, logic_expr)
		ctx.modify_instr(item, new_item)
		return False

scheme = ReplacingScheme("propagate_error", pattern)

add_storage_scheme(scheme)