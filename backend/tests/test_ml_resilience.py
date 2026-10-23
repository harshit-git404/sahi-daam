import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.ml.produce_classifier import _is_network_error, load_produce_classifier, is_produce_classifier_loaded
from backend.main import load_ml_models



class TestMLResilience(unittest.TestCase):
    """Tests ensuring optional ML model startup resilience and non-suppression of programming errors."""

    def test_is_network_error_detection(self):
        # Direct network exceptions
        self.assertTrue(_is_network_error(ConnectionError("Connection reset by peer")))
        self.assertTrue(_is_network_error(TimeoutError("Request timed out")))
        self.assertTrue(_is_network_error(OSError("We couldn't connect to 'https://huggingface.co' to load this file")))
        self.assertTrue(_is_network_error(OSError("Failed to establish a new connection: [Errno 11001] getaddrinfo failed")))

        # Wrapped exception via cause or context
        wrapped = RuntimeError("Loading failed")
        wrapped.__cause__ = ConnectionError("Offline")
        self.assertTrue(_is_network_error(wrapped))

        # Programming errors must NOT be classified as network errors
        self.assertFalse(_is_network_error(TypeError("unsupported operand type")))
        self.assertFalse(_is_network_error(ValueError("invalid literal for int()")))
        self.assertFalse(_is_network_error(AttributeError("'NoneType' object has no attribute 'config'")))
        self.assertFalse(_is_network_error(ZeroDivisionError("division by zero")))

    @patch("backend.ml.produce_classifier._get_model")
    def test_load_produce_classifier_network_failure_does_not_crash(self, mock_get_model):
        """A network failure while loading the optional HF model must log and return False without crashing."""
        net_err = ConnectionError("Could not reach huggingface.co")
        mock_get_model.side_effect = RuntimeError(f"Produce classifier could not be loaded: {net_err}")
        mock_get_model.side_effect.__cause__ = net_err

        result = load_produce_classifier()
        self.assertFalse(result)

    @patch("backend.ml.produce_classifier._get_model")
    def test_load_produce_classifier_programming_error_is_raised(self, mock_get_model):
        """A programming error (e.g. bug in model initialization) must NOT be suppressed."""
        prog_err = TypeError("Invalid argument 'num_labels'")
        mock_get_model.side_effect = RuntimeError(f"Produce classifier could not be loaded: {prog_err}")
        mock_get_model.side_effect.__cause__ = prog_err

        with self.assertRaises(RuntimeError):
            load_produce_classifier()

    @patch("backend.ml.produce_classifier._get_model")
    def test_load_produce_classifier_success(self, mock_get_model):
        mock_get_model.return_value = (MagicMock(), MagicMock())
        result = load_produce_classifier()
        self.assertTrue(result)

    @patch("backend.main.load_produce_classifier")
    @patch("backend.main.load_freshness_model")
    def test_main_startup_with_offline_classifier(self, mock_freshness, mock_classifier):
        """When optional produce classifier is offline, startup completes safely without claiming success."""
        mock_classifier.return_value = False
        mock_freshness.return_value = None

        with self.assertLogs("backend.main", level="WARNING") as log_capture:
            load_ml_models()
            self.assertTrue(any("Produce classifier is unavailable" in msg for msg in log_capture.output))


if __name__ == "__main__":
    unittest.main()
