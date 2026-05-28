import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)
_model = None


def get_embedding_model():
    global _model
    if _model is None:
        logger.info("loading embedding model %s", settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def generate_embedding(text):
    model = get_embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return np.array(vector, dtype=np.float32)


def generate_embeddings_batch(text_list):
    model = get_embedding_model()
    vectors = model.encode(text_list, normalize_embeddings=True)
    return [np.array(v, dtype=np.float32) for v in vectors]
