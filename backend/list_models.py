import logging

from ml.freshness_model import load_freshness_model
from ml.produce_classifier import load_produce_classifier

logging.basicConfig(level=logging.INFO)
load_produce_classifier()
load_freshness_model()
print("Local produce classifier and freshness model loaded.")
