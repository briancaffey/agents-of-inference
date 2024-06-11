import unittest
from agents_of_inference.comfyui.faceid import generate_img_with_face

# TODO: finish this test
class TestGenerateImgWithFace(unittest.TestCase):
    def test_generate_img_with_face(self):
        # Set up input parameters and expected output
        input_params = "1717913528", "test prompt", "000.png", "000"  # Provide the required input parameters
        # expected_output = ...  # Provide the expected output

        # Call the function under test
        actual_output = generate_img_with_face(input_params)

        assert False
