from libs.utils.imports import *

class list(list):
	def get(self, element):
		for i in range(len(self)):
			if self[i] == element:
				return i
		return -1
	def delete(self, element):
		if element in self: self.remove(element)