import glm
import math
class Quaternion:

	def normalize(self):
		mag = math.sqrt(self.x**2 + self.y**2 + self.z**2 + self.w**2)
		self.x/=mag
		self.y/=mag
		self.z/=mag
		self.w/=mag

	def to_matrix(self):
		mat = glm.mat4(1.0)
		xy = self.x * self.y
		xz = self.x * self.z
		xw = self.x * self.w
		yz = self.y * self.z
		yw = self.y * self.w
		zw = self.z * self.w

		mat[0].x = 1 - 2 * (self.y**2 + self.z**2)
		mat[0].y = 2 * (xy - zw)
		mat[0].z = 2 * (xz + yw)

		mat[1].x = 2 * (xy + zw)
		mat[1].y = 1 - 2 * (self.x**2 + self.z**2)
		mat[1].z = 2 * (yz - xw)

		mat[2].x = 2 * (xz - yw)
		mat[2].y = 2 * (yz + xw)
		mat[2].z = 1 - 2 * (self.x**2 + self.y**2)

		return mat

	def __init__(self, matrix=None):

		self.x = 0
		self.y = 0
		self.z = 0
		self.w = 1

		if matrix:
			diag = matrix[0].x + matrix[1].y + matrix[2].z
			if diag > 0:
				w4 = float(math.sqrt(diag + 1) * 2)
				self.w = w4/4
				self.x = (matrix[2].y - matrix[1].z) / w4
				self.y = (matrix[0].z - matrix[2].x) / w4
				self.z = (matrix[1].x - matrix[0].y) / w4
			elif matrix[0].x > matrix[1].y and matrix[0].x > matrix[2].z:
				x4 = float(math.sqrt(1 + matrix[0].x - matrix[1].y - matrix[2].z) * 2)
				self.w = (matrix[2].y - matrix[1].z) / x4
				self.x = x4/4
				self.y = (matrix[1].x + matrix[0].y) / w4
				self.z = (matrix[0].z + matrix[2].x) / w4
			elif matrix[1].y > matrix[2].z:
				y4 = float(math.sqrt(1 + matrix[1].y - matrix[0].x - matrix[2].z) * 2)
				self.w = (matrix[0].z - matrix[2].x) / y4
				self.x = (matrix[1].x + matrix[0].y) / y4
				self.y = y4/4
				self.z = (matrix[2].y + matrix[1].z) / y4
			else:
				z4 = float(math.sqrt(1 + matrix[2].z - matrix[0].x - matrix[1].y) * 2)
				self.w = (matrix[1].x - matrix[0].y) / z4
				self.x = (matrix[0].z + matrix[2].x) / z4
				self.y = (matrix[1].z + matrix[2].y) / z4
				self.z = z4/4

		self.normalize()

	def interpolate(a, b, blend):
		q = Quaternion()
		dot = a.w * b.w + a.x * b.x + a.y * b.y + a.z * b.z
		blendI = 1 - blend
		if dot < 0:
			q.w = blendI * a.w + blend * -b.w
			q.x = blendI * a.x + blend * -b.x
			q.y = blendI * a.y + blend * -b.y
			q.z = blendI * a.z + blend * -b.z
		else:
			q.w = blendI * a.w + blend * b.w
			q.x = blendI * a.x + blend * b.x
			q.y = blendI * a.y + blend * b.y
			q.z = blendI * a.z + blend * b.z
		q.normalize()
		return q

mat = glm.mat4(0.791042, 0.414291, 0.377793, 0,
				-5.06072, 1.1451, -5.02336, -4.00456,
				3.24019, -0.11562, 4.3599, 3.1254,
				1.18574, -0.0957919, 1.15946, 1)
quat = Quaternion(mat)
quat2 = glm.quat_cast(mat)

pos = glm.vec3(mat[3].x, mat[3].y, mat[3].z)
mat2 = glm.mat4(1.0)
mat2 = glm.translate(mat2, pos)
mat2 = mat2 * quat.to_matrix()

print(mat)
print()
print(mat2)

