from typing import List, Any, Dict

class Encoder:
    """
    A class dedicated to creating or defining encoder objects.
    """

    def encode_boolean_vector(self, vector: List[int]) -> Dict[str, Any]:
        """
        Given a vector for BOOLEAN data, return the "encoder" structure.
        E.g.:
          {
            "type": "int",
            "data": [ <vector values> ]
          }
        """
        return {
            "type": "int",
            "data": vector
        }
