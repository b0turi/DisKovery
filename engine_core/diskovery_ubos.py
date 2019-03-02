
import glm
from ctypes import c_float, sizeof
from abc import ABC, abstractmethod

_matrix_type = (c_float*4)*4

class UniformBufferObject(ABC):
	@abstractmethod
	def get_data(self):
		pass

	@abstractmethod
	def get_size():
		pass

def get_matrix_data(matrix):
	m_data = ((c_float*4)*4)()

	for i, row in enumerate(matrix):
		row_data = (c_float*4)(*row)
		m_data[i] = row_data

	return m_data

class MVPMatrix(UniformBufferObject):
	"""
	A uniform filler that holds data for the model (aka world), view, and 
	projection matrices to be used when positioning an entity in world space.

	**Attributes of the MVPMatrix class:**

	.. py:attribute:: model

		A 4x4 Matrix that stores the position, rotation, and scale of an Entity
		within the game world.

	.. py:attribute:: view

		A 4x4 Matrix that stores information about the position and rotation of
		the Camera. The model matrix is shown relative to the view matrix, and the
		two are multiplied together in the vertex shader to achieve this.

	.. py:attribute:: projection

		A 4x4 Matrix that establishes the perspective and depth of the 3D scene.
		Actually maps the positions given by the model and view matrices so they
		are shown in 3D and not native Vulkan coordinates. It is multiplied by the
		previous two matrices in the vertex shader to achieve this.

	.. note:: To learn more about how these matrices are used, check out this_
		article on CodingLabs.net that includes descriptions of how translations,
		rotations, and scaling operations are applied via matrices, as well as
		how the view matrix acts as the Camera, and the projection determines
		how the scene will actually look.

	.. _this: http://www.codinglabs.net/article_world_view_projection_matrix.aspx

	**Methods of the MVPMatrix class:**
	"""
	def __init__(self):
		self.model = glm.mat4()
		self.view = glm.mat4()
		self.projection = glm.mat4()

	def get_data(self):
		"""
		Takes the information stored in the matrices of this class and 
		condenses them into a ``ctypes`` array for passing through a
		:class:`~diskovery_buffer.UniformBuffer`.

		:returns: The data stored in the matrices of this class as a ``Mat4_Array_3``
		"""
		matrices = (_matrix_type*3)(
			get_matrix_data(self.model),
			get_matrix_data(self.view),
			get_matrix_data(self.projection)
		)
		return matrices

	@staticmethod
	def get_size():
		return sizeof(_matrix_type) * 3

MAX_JOINTS = 50
class JointData(UniformBufferObject):
	def __init__(self):
		self.joint_data = (_matrix_type * MAX_JOINTS)()

	@staticmethod
	def get_data(self):
		return self.joint_data

	@staticmethod
	def get_size():
		return sizeof(_matrix_type) * MAX_JOINTS