from utils.files.apply_patch import apply_patch


def test_apply_patch():
    original_text = """numpy
pyqt5
hydra-core
torch
torchvision
torchaudio
tensorflow-tensorboard
tensorboardx"""

    diff_text = "--- requirements.pytorch.txt\n+++ requirements.pytorch.txt\n@@ -2,1 +2,1 @@\n-pyqt5\n+pyqt6\n"

    expected_result = """numpy
pyqt6
hydra-core
torch
torchvision
torchaudio
tensorflow-tensorboard
tensorboardx
"""

    modified_text, _message = apply_patch(original_text, diff_text)

    assert modified_text == expected_result
