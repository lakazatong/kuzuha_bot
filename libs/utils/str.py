class str(str):
	def finds(self, substring):
		start = 0
		indices = []
		while True:
			index = self.find(substring, start)
			if index == -1:
				break
			indices.append(index)
			start = index + len(substring)
		return indices
