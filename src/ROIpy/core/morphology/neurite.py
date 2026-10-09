from __future__ import annotations
import math
import numpy as np
from ROIpy.analysis.stats import calculate_total_length
from ROIpy.core.morphology.node import Node


class Neurite:
    """
    Representation of a single neurite.

    This class encapsulates the properties and nodes of a single neurite,
    including branch degree, ID, and total length.
    """

    def __init__(
            self,
            nodes: list,
            branch_degree: int,
            branch_id: int,
            branch_length: float,
    ) -> None:
        """
        Initialize a Neurite instance.

        Parameters
        ----------
        nodes : list
            List of nodes comprising this neurite.
        branch_degree : int
            Degree of the branch to which the neurite belongs.
        branch_id : int
            Unique identifier for the neurite.
        branch_length : float
            Total length of the neurite.
        """
        self.nodes = nodes
        self.id = branch_id
        self.degree = int(branch_degree)
        self.compartment = self.nodes[0].type
        self.length = branch_length
        self.mean_radius = self._mean_radius()

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, index):
        return self.nodes[index]

    def __iter__(self):
        return iter(self.nodes)

    def _mean_radius(self):
        return np.mean([node.radius for node in self.nodes])

    def totlen(self) -> float:
        """
        Calculate the total length of the neurites.

        Returns
        -------
        float
            Total length of neurites in micrometers (µm).
        """
        return calculate_total_length(self.nodes)

    def flat(
            self,
            direction: str = "horizontal",
            return_params: bool = False
    ) -> tuple:
        """
        Flatten the branch so that its first and last nodes
        align along a straight line, while preserving inter-node distances.

        Parameters
        ----------
        direction : str, optional
            Direction of flattening.

        Returns
        -------
        tuple
            A tuple containing the rotation angle and a
            list of Node objects with updated x, y coordinates.

        Raises
        ------
        ValueError
            If an invalid direction is provided.
        """

        if direction not in ["horizontal", "vertical"]:
            raise ValueError(
                "Invalid direction. Choose 'horizontal' or 'vertical'.")

        branch_copy = [
            Node.from_dict(node.to_dict()) for node in self.nodes]

        nodes = sorted(
            branch_copy, key=lambda node: node.id)

        first_node = nodes[0]
        last_node = nodes[-1]

        # Translate first node to (0, 0)
        translation_x = -first_node.x
        translation_y = -first_node.y

        for node in branch_copy:
            node.x += translation_x
            node.y += translation_y

        # Calculate the angle for alignment
        delta_x = last_node.x
        delta_y = last_node.y
        angle = math.atan2(delta_y, delta_x)

        if direction == "vertical":
            angle -= math.pi / 2

        if return_params:
            return (translation_x, translation_y), angle

        # Compute rotation matrix
        cos_theta = math.cos(-angle)
        sin_theta = math.sin(-angle)
        rotation_matrix = np.array(
            [[cos_theta, -sin_theta],
             [sin_theta, cos_theta]])

        # Rotate all nodes
        for node in branch_copy:
            original_coords = np.array([node.x, node.y])
            rotated_coords = rotation_matrix.dot(original_coords)
            node.x, node.y = (
                round(rotated_coords[0], 6),
                round(rotated_coords[1], 6))
        
        return branch_copy
