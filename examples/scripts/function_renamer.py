from __future__ import annotations
import idaapi
from herapi import *


class FunctionRenamer(Scheme):
	def __init__(self, debug_flag:int):
		pattern = IfPat(
			debug_flag,
			DeepExprPat(CallPat("printf", ignore_arguments=True), bind_name="debug_print"),
			should_wrap_in_block=False, # if to not wrap in block, because we want to search inside block's instructions
		)
		super().__init__(pattern)
		self.renamings = {}
		self.conflicts = {}

	def on_matched_item(self, item, ctx: MatchContext) -> ASTPatch|None:
		func_ea = ctx.ast_ctx.func_addr
		debug_print = ctx.get_item("debug_print")
		s = debug_print.a[1]
		name = s.print1(None)
		name = idaapi.tag_remove(name)
		name = idaapi.str2user(name)
		name = name[2:-2]
		self.add_renaming(func_ea, name)
		return None

	def add_renaming(self, func_addr, new_name):
		current_name = idaapi.get_func_name(func_addr) 
		if current_name == new_name:
			return

		if func_addr in self.conflicts:
			self.conflicts[func_addr].add(new_name)
			return

		current = self.renamings.get(func_addr)
		if current is not None and current != new_name:
			del self.renamings[func_addr]
			self.conflicts[func_addr] = {current, new_name}
			return

		self.renamings[func_addr] = new_name

	def apply_renamings(self):
		for func_addr, new_name in self.renamings.items():
			print("renaming", hex(func_addr), "to", new_name)
			idaapi.set_name(func_addr, new_name)

	def print_conflicts(self):
		for func_addr, names in self.conflicts.items():
			print("Conflicting renamings:", hex(func_addr), names)


def do_renames(debug_flag: int):
	scheme = FunctionRenamer(debug_flag)
	match_objects_xrefs(scheme, debug_flag)
	scheme.apply_renamings()
	scheme.print_conflicts()
