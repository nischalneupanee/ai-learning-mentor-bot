"""
Text analysis utilities for qualifying and analyzing learning messages.
"""

import re
from typing import Optional
from difflib import SequenceMatcher
from collections import Counter
import logging

logger = logging.getLogger(__name__)


# Technical keywords for depth detection
TECHNICAL_KEYWORDS = {
    # AI General
    "artificial intelligence", "neural network", "deep learning", "machine learning",
    "reinforcement learning", "supervised learning", "unsupervised learning",
    "natural language processing", "computer vision", "generative ai",
    
    # ML Algorithms
    "linear regression", "logistic regression", "decision tree", "random forest",
    "gradient boosting", "xgboost", "lightgbm", "catboost", "svm", "support vector",
    "naive bayes", "k-means", "clustering", "classification", "regression",
    "ensemble", "bagging", "boosting", "cross-validation", "hyperparameter",
    
    # Deep Learning
    "cnn", "rnn", "lstm", "gru", "transformer", "attention mechanism",
    "self-attention", "multi-head attention", "encoder", "decoder",
    "autoencoder", "variational autoencoder", "vae", "gan", "generative adversarial",
    "diffusion model", "stable diffusion", "convolution", "pooling", "dropout",
    "batch normalization", "layer normalization", "residual connection",
    "skip connection", "feedforward", "backpropagation", "gradient descent",
    "optimizer", "adam", "sgd", "learning rate", "loss function", "activation function",
    "relu", "sigmoid", "softmax", "tanh", "gelu",
    
    # NLP
    "tokenization", "embedding", "word2vec", "glove", "fasttext", "bert", "gpt",
    "llm", "large language model", "fine-tuning", "prompt engineering",
    "rag", "retrieval augmented", "semantic search", "text classification",
    "named entity recognition", "ner", "sentiment analysis", "summarization",
    
    # Computer Vision  
    "image classification", "object detection", "segmentation", "yolo",
    "resnet", "vgg", "inception", "efficientnet", "feature extraction",
    "data augmentation", "transfer learning",
    
    # Data Science
    "exploratory data analysis", "eda", "feature engineering", "feature selection",
    "data preprocessing", "data cleaning", "missing values", "outlier detection",
    "normalization", "standardization", "one-hot encoding", "label encoding",
    "train test split", "overfitting", "underfitting", "bias variance",
    "confusion matrix", "precision", "recall", "f1 score", "roc auc",
    "accuracy", "cross entropy", "mse", "mae", "rmse",
    
    # Frameworks & Libraries
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "pandas",
    "numpy", "matplotlib", "seaborn", "huggingface", "transformers",
    "langchain", "llamaindex", "opencv", "spacy", "nltk",
    
    # MLOps
    "mlflow", "wandb", "tensorboard", "model deployment", "inference",
    "model serving", "containerization", "docker", "kubernetes",
    "feature store", "model registry", "a/b testing", "canary deployment",
    
    # Mathematics
    "linear algebra", "matrix", "vector", "tensor", "gradient", "derivative",
    "partial derivative", "chain rule", "jacobian", "hessian", "eigenvalue",
    "eigenvector", "probability", "statistics", "bayesian", "prior", "posterior",
    "likelihood", "distribution", "gaussian", "normal distribution",
    "cost function", "objective function", "optimization",
}

# Topic classification keywords
TOPIC_KEYWORDS = {
    "AI": {
        "artificial intelligence", "ai", "intelligent systems", "expert systems",
        "knowledge representation", "reasoning", "planning", "agents",
        "multi-agent", "cognitive", "symbolic ai", "neural-symbolic",
    },
    "ML": {
        "machine learning", "ml", "supervised", "unsupervised", "semi-supervised",
        "classification", "regression", "clustering", "dimensionality reduction",
        "feature engineering", "model selection", "hyperparameter tuning",
        "ensemble methods", "cross-validation", "bias-variance",
    },
    "DL": {
        "deep learning", "neural network", "cnn", "rnn", "lstm", "transformer",
        "attention", "encoder", "decoder", "autoencoder", "gan", "vae",
        "convolution", "backpropagation", "gpu", "cuda", "pytorch", "tensorflow",
    },
    "DS": {
        "data science", "data analysis", "exploratory", "eda", "visualization",
        "pandas", "statistics", "hypothesis testing", "a/b test",
        "data cleaning", "data wrangling", "etl", "sql", "data pipeline",
    },
}


def qualifies_as_log(message_content: str, min_length: int = 30) -> tuple[bool, str]:
    """
    Check if a message qualifies as a valid learning log.
    
    Returns:
        Tuple of (qualifies, reason)
    """
    # Check length
    if len(message_content.strip()) < min_length:
        return False, f"Too short ({len(message_content)} < {min_length} chars)"
    
    # Check if it's mostly punctuation or special characters
    alpha_count = sum(1 for c in message_content if c.isalpha())
    if alpha_count < min_length // 2:
        return False, "Insufficient alphabetic content"
    
    # Check if it's a URL dump
    url_pattern = r'https?://\S+'
    text_without_urls = re.sub(url_pattern, '', message_content)
    if len(text_without_urls.strip()) < min_length // 2:
        return False, "Mostly URLs"
    
    return True, "Qualified"


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate text similarity ratio between two strings.
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()
    
    return SequenceMatcher(None, t1, t2).ratio()


def is_duplicate_content(
    new_content: str,
    existing_contents: list[str],
    threshold: float = 0.85
) -> bool:
    """
    Check if new content is too similar to existing contents.
    """
    new_normalized = new_content.lower().strip()
    
    for existing in existing_contents:
        similarity = calculate_similarity(new_normalized, existing)
        if similarity >= threshold:
            return True
    
    return False


def detect_technical_depth(text: str) -> tuple[int, list[str]]:
    """
    Detect technical depth and return score with found keywords.
    
    Returns:
        Tuple of (depth_score 0-5, list of technical terms found)
    """
    text_lower = text.lower()
    found_keywords = []
    
    # Check for technical keywords
    for keyword in TECHNICAL_KEYWORDS:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    # Check for code patterns
    code_patterns = [
        r'\b(def|class|import|from|return)\b',  # Python
        r'\b(function|const|let|var|async)\b',   # JavaScript
        r'[\w]+\s*\([^)]*\)',                     # Function calls
        r'[\w]+\s*=\s*[\w\[\{]',                  # Assignments
        r'```[\s\S]*?```',                        # Code blocks
    ]
    
    code_score = 0
    for pattern in code_patterns:
        if re.search(pattern, text):
            code_score += 1
    
    # Calculate depth score (0-5)
    keyword_score = min(len(found_keywords), 10) // 2  # Max 5 from keywords
    combined_score = min(keyword_score + code_score, 5)
    
    return combined_score, found_keywords[:10]  # Limit returned keywords


def classify_topic(text: str) -> tuple[str, dict[str, float]]:
    """
    Classify the primary topic and return confidence scores for each topic.
    
    Returns:
        Tuple of (primary_topic, {topic: confidence})
    """
    text_lower = text.lower()
    topic_scores = {}
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                score += 1
        topic_scores[topic] = score
    
    total = sum(topic_scores.values())
    if total == 0:
        return "Mixed", {t: 0.25 for t in TOPIC_KEYWORDS}
    
    # Normalize to confidence scores
    confidences = {t: score / total for t, score in topic_scores.items()}
    
    # Find primary topic
    primary = max(topic_scores, key=topic_scores.get)
    
    # If scores are too close, mark as Mixed
    sorted_scores = sorted(topic_scores.values(), reverse=True)
    if len(sorted_scores) >= 2 and sorted_scores[0] - sorted_scores[1] <= 1:
        primary = "Mixed"
    
    return primary, confidences


def extract_concepts(text: str, max_concepts: int = 10) -> list[str]:
    """
    Extract learning concepts from text.
    """
    text_lower = text.lower()
    found_concepts = []
    
    # Check for technical keywords
    for keyword in TECHNICAL_KEYWORDS:
        if keyword in text_lower:
            found_concepts.append(keyword)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_concepts = []
    for concept in found_concepts:
        if concept not in seen:
            seen.add(concept)
            unique_concepts.append(concept)
    
    return unique_concepts[:max_concepts]


def update_concept_frequency(
    existing_freq: dict[str, int],
    new_concepts: list[str]
) -> dict[str, int]:
    """
    Update concept frequency map with new concepts.
    """
    updated = existing_freq.copy()
    for concept in new_concepts:
        updated[concept] = updated.get(concept, 0) + 1
    return updated


def calculate_concept_repetition_penalty(
    new_concepts: list[str],
    concept_frequency: dict[str, int],
    threshold: int = 3
) -> tuple[float, list[str]]:
    """
    Calculate penalty for repeated concepts.
    
    Returns:
        Tuple of (penalty_multiplier 0.5-1.0, repeated_concepts)
    """
    repeated = []
    
    for concept in new_concepts:
        freq = concept_frequency.get(concept, 0)
        if freq >= threshold:
            repeated.append(concept)
    
    if not new_concepts:
        return 1.0, []
    
    repetition_ratio = len(repeated) / len(new_concepts)
    penalty = max(0.5, 1.0 - (repetition_ratio * 0.5))
    
    return penalty, repeated


def summarize_logs(logs: list[str], max_length: int = 2000) -> str:
    """
    Summarize multiple logs into a single text for AI processing.
    """
    combined = "\n---\n".join(logs)
    
    if len(combined) <= max_length:
        return combined
    
    # Truncate intelligently
    truncated = combined[:max_length]
    last_break = truncated.rfind("\n---\n")
    
    if last_break > max_length // 2:
        truncated = truncated[:last_break]
    
    return truncated + "\n[... additional logs truncated ...]"


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def get_reading_time(text: str, wpm: int = 200) -> int:
    """Estimate reading time in minutes."""
    words = count_words(text)
    return max(1, words // wpm)


def clean_message_content(content: str) -> str:
    """
    Clean message content for analysis.
    Removes Discord-specific formatting.
    """
    # Remove mentions
    content = re.sub(r'<@!?\d+>', '', content)
    content = re.sub(r'<#\d+>', '', content)
    content = re.sub(r'<@&\d+>', '', content)
    
    # Remove custom emojis
    content = re.sub(r'<a?:\w+:\d+>', '', content)
    
    # Remove extra whitespace
    content = ' '.join(content.split())
    
    return content.strip()


def format_concepts_display(concepts: list[str], max_display: int = 5) -> str:
    """Format concepts for display in embed."""
    if not concepts:
        return "None detected"
    
    displayed = concepts[:max_display]
    formatted = ", ".join(f"`{c}`" for c in displayed)
    
    if len(concepts) > max_display:
        formatted += f" +{len(concepts) - max_display} more"
    
    return formatted


def analyze_message(content: str, existing_logs: list[str] = None) -> dict:
    """
    Comprehensive analysis of a learning message.
    
    Returns dict with:
        - qualifies: bool
        - reason: str
        - is_duplicate: bool
        - depth_score: int
        - technical_terms: list
        - primary_topic: str
        - topic_confidences: dict
        - concepts: list
        - word_count: int
    """
    existing_logs = existing_logs or []
    
    # Clean content
    cleaned = clean_message_content(content)
    
    # Check qualification
    qualifies, reason = qualifies_as_log(cleaned)
    
    # Check duplicate
    is_dup = is_duplicate_content(cleaned, existing_logs)
    
    # Detect depth
    depth, terms = detect_technical_depth(cleaned)
    
    # Classify topic
    topic, confidences = classify_topic(cleaned)
    
    # Extract concepts
    concepts = extract_concepts(cleaned)
    
    return {
        "qualifies": qualifies and not is_dup,
        "reason": reason if not qualifies else ("Duplicate" if is_dup else "Qualified"),
        "is_duplicate": is_dup,
        "depth_score": depth,
        "technical_terms": terms,
        "primary_topic": topic,
        "topic_confidences": confidences,
        "concepts": concepts,
        "word_count": count_words(cleaned),
    }
