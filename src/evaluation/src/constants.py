import os


DATASET_ROOT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "data"
)
EXPERIMENT_ROOT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "evaluation"
)

COSINE_SIMILARITY_ID = '1d444d72-ff6f-45d7-bcdb-c64acbfdf5d0/models/Cosine_Similarity-Evaluator'
CORR_ID = '1d444d72-ff6f-45d7-bcdb-c64acbfdf5d0/models/CorrectnessEvaluator'
TOKEN_LATENCY_ID = '1d444d72-ff6f-45d7-bcdb-c64acbfdf5d0/models/Token-Usage-Latency-Evaluator'
