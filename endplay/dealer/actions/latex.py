from endplay.dealer.actions.base import BaseActions

class LaTeXActions(BaseActions):
	def __init__(self, deals, stream):
		super().__init__(deals, stream)
		self.write = lambda *objs, **kwargs: print(*objs, **kwargs, file=self.stream)

	def preamble(self):
		self.write(r"\documentclass[12pt]{article}")
		self.write(r"\usepackage[left=20mm,right=20mm,top=20mm,bottom=20mm]{geometry}")
		self.write(r"\usepackage{graphicx}")
		self.write(r"\begin{document}")
		self.write(r"\noindent")

	def postamble(self):
		self.write(r"\end{document}")
		self.write()

	def printall(self):
		for deal in self.deals:
			self.write(r"\resizebox{0.33\textwidth}{!}{" + deal.to_LaTeX() + "}")