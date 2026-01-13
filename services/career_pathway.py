"""
Career Pathway System for AI/ML Engineers and Researchers.
Defines milestones, skills, and progression paths.
"""

# Career Pathways
CAREER_PATHS = {
    "ml_engineer": {
        "name": "Machine Learning Engineer",
        "emoji": "⚙️",
        "description": "Build and deploy ML systems in production",
        "skills": [
            "Python Programming",
            "Data Preprocessing",
            "Model Training",
            "Model Deployment",
            "MLOps",
            "Cloud Platforms",
            "API Development",
            "System Design"
        ]
    },
    "ai_researcher": {
        "name": "AI Researcher",
        "emoji": "🔬",
        "description": "Push boundaries of AI through research",
        "skills": [
            "Mathematics",
            "Deep Learning Theory",
            "Research Methods",
            "Paper Reading",
            "Experimentation",
            "Novel Architectures",
            "Writing Papers",
            "Theoretical Analysis"
        ]
    }
}

# Learning Pathway Milestones
PATHWAY_MILESTONES = {
    # Beginner Level (0-500 points)
    "foundations": {
        "level": 0,
        "name": "🌱 Foundations",
        "points_range": (0, 500),
        "focus_areas": [
            "Python basics and data structures",
            "NumPy and Pandas fundamentals",
            "Basic statistics and linear algebra",
            "Introduction to ML concepts",
            "Data visualization with Matplotlib/Seaborn"
        ],
        "ml_engineer_goals": [
            "Master Python fundamentals",
            "Learn data manipulation with Pandas",
            "Understand basic ML algorithms (Linear Regression, Decision Trees)"
        ],
        "researcher_goals": [
            "Build strong mathematical foundation",
            "Read introductory ML papers",
            "Understand basic neural network theory"
        ],
        "recommended_projects": [
            "Iris flower classification",
            "House price prediction",
            "Titanic survival prediction"
        ]
    },
    
    # Intermediate Level (500-2000 points)
    "intermediate": {
        "level": 1,
        "name": "📚 Intermediate Practitioner",
        "points_range": (500, 2000),
        "focus_areas": [
            "Supervised learning algorithms",
            "Model evaluation and validation",
            "Feature engineering techniques",
            "Introduction to deep learning",
            "CNNs and computer vision basics"
        ],
        "ml_engineer_goals": [
            "Build end-to-end ML pipelines",
            "Learn model deployment with Flask/FastAPI",
            "Understand Docker basics",
            "Practice feature engineering"
        ],
        "researcher_goals": [
            "Read foundational papers (AlexNet, ResNet, Attention)",
            "Implement papers from scratch",
            "Experiment with different architectures",
            "Learn PyTorch/TensorFlow deeply"
        ],
        "recommended_projects": [
            "Image classifier with CNNs",
            "Sentiment analysis with NLP",
            "Deploy ML model as REST API"
        ]
    },
    
    # Advanced Level (2000-5000 points)
    "advanced": {
        "level": 2,
        "name": "🚀 Advanced Specialist",
        "points_range": (2000, 5000),
        "focus_areas": [
            "Advanced deep learning (Transformers, GANs)",
            "NLP with large language models",
            "Reinforcement learning",
            "MLOps and production systems",
            "Advanced optimization techniques"
        ],
        "ml_engineer_goals": [
            "Build scalable ML systems",
            "Implement CI/CD for ML models",
            "Master Kubernetes and cloud deployment",
            "Design robust data pipelines",
            "A/B testing and model monitoring"
        ],
        "researcher_goals": [
            "Read and implement recent papers (< 1 year old)",
            "Design novel architectures",
            "Conduct ablation studies",
            "Write technical blog posts/papers",
            "Reproduce SOTA results"
        ],
        "recommended_projects": [
            "Build a chatbot with transformers",
            "Image generation with GANs or Diffusion Models",
            "Deploy production ML system with monitoring"
        ]
    },
    
    # Researcher Level (5000+ points)
    "researcher": {
        "level": 3,
        "name": "🎓 Research Expert",
        "points_range": (5000, float('inf')),
        "focus_areas": [
            "Cutting-edge research areas",
            "Novel model architectures",
            "Theoretical foundations",
            "Research paper writing",
            "Open source contributions"
        ],
        "ml_engineer_goals": [
            "Architect ML platforms",
            "Lead ML teams",
            "Contribute to open-source ML tools",
            "Design custom training frameworks",
            "Optimize large-scale systems"
        ],
        "researcher_goals": [
            "Publish papers at top conferences",
            "Propose novel research directions",
            "Mentor other researchers",
            "Review papers for conferences",
            "Push state-of-the-art forward"
        ],
        "recommended_projects": [
            "Implement novel research idea",
            "Reproduce and improve SOTA results",
            "Contribute to major ML framework (PyTorch, JAX)"
        ]
    }
}

# Topic-specific learning paths
TOPIC_ROADMAPS = {
    "AI": {
        "beginner": ["Search algorithms", "Planning", "Knowledge representation"],
        "intermediate": ["Expert systems", "Logic and reasoning", "Intelligent agents"],
        "advanced": ["Multi-agent systems", "Game AI", "Automated planning"]
    },
    "ML": {
        "beginner": ["Linear regression", "Logistic regression", "Decision trees"],
        "intermediate": ["Random forests", "SVM", "Ensemble methods", "Feature selection"],
        "advanced": ["AutoML", "Transfer learning", "Meta-learning"]
    },
    "DL": {
        "beginner": ["Neural networks", "Backpropagation", "CNNs"],
        "intermediate": ["RNNs", "LSTMs", "Attention mechanisms", "Transformers"],
        "advanced": ["GANs", "Diffusion models", "Vision transformers", "Few-shot learning"]
    },
    "DS": {
        "beginner": ["Data cleaning", "EDA", "Statistics", "Visualization"],
        "intermediate": ["A/B testing", "Time series", "Dimensionality reduction"],
        "advanced": ["Causal inference", "Bayesian methods", "Large-scale data processing"]
    }
}

# Skill tree with dependencies
SKILL_TREE = {
    "python_basics": {
        "name": "Python Fundamentals",
        "prerequisites": [],
        "unlocks": ["data_manipulation", "ml_basics"]
    },
    "data_manipulation": {
        "name": "Data Manipulation (Pandas, NumPy)",
        "prerequisites": ["python_basics"],
        "unlocks": ["ml_basics", "visualization"]
    },
    "ml_basics": {
        "name": "ML Fundamentals",
        "prerequisites": ["python_basics", "data_manipulation"],
        "unlocks": ["supervised_learning", "unsupervised_learning"]
    },
    "deep_learning": {
        "name": "Deep Learning",
        "prerequisites": ["ml_basics", "linear_algebra"],
        "unlocks": ["cv", "nlp", "research"]
    },
    "deployment": {
        "name": "Model Deployment",
        "prerequisites": ["ml_basics"],
        "unlocks": ["mlops", "production_systems"]
    },
    "research": {
        "name": "Research Skills",
        "prerequisites": ["deep_learning"],
        "unlocks": ["paper_writing", "sota_replication"]
    }
}

def get_milestone_for_points(points: int) -> dict:
    """Get current milestone based on points."""
    for milestone_id, milestone in PATHWAY_MILESTONES.items():
        min_points, max_points = milestone["points_range"]
        if min_points <= points < max_points:
            return {"id": milestone_id, **milestone}
    
    # Return highest milestone if beyond all ranges
    return {"id": "researcher", **PATHWAY_MILESTONES["researcher"]}

def get_next_milestone(current_points: int) -> dict:
    """Get the next milestone to achieve."""
    for milestone_id, milestone in PATHWAY_MILESTONES.items():
        min_points, max_points = milestone["points_range"]
        if current_points < min_points:
            return {"id": milestone_id, **milestone}
    
    return None  # Already at max level

def get_recommendations_for_level(skill_level: int, topic_coverage: dict, career_path: str = "ml_engineer") -> list:
    """Get personalized recommendations based on current level and weak areas."""
    recommendations = []
    
    # Get current milestone
    milestone_keys = list(PATHWAY_MILESTONES.keys())
    if skill_level < len(milestone_keys):
        milestone = PATHWAY_MILESTONES[milestone_keys[skill_level]]
        
        # Get career-specific goals
        if career_path == "ml_engineer":
            recommendations.extend(milestone.get("ml_engineer_goals", []))
        else:
            recommendations.extend(milestone.get("researcher_goals", []))
    
    # Identify weak topics
    weak_topics = [topic for topic, count in topic_coverage.items() if count < 5]
    
    for topic in weak_topics:
        if topic in TOPIC_ROADMAPS:
            level_key = ["beginner", "intermediate", "advanced"][min(skill_level, 2)]
            topic_items = TOPIC_ROADMAPS[topic].get(level_key, [])
            recommendations.extend([f"Study {topic}: {item}" for item in topic_items[:2]])
    
    return recommendations[:5]  # Return top 5

def get_progress_summary(user_data: dict) -> dict:
    """Generate a progress summary with pathway information."""
    points = user_data.get("points", 0)
    skill_level = user_data.get("skill_level", 0)
    topic_coverage = user_data.get("topic_coverage", {})
    
    current_milestone = get_milestone_for_points(points)
    next_milestone = get_next_milestone(points)
    
    # Calculate overall progress percentage
    if next_milestone:
        current_min = current_milestone["points_range"][0]
        next_min = next_milestone["points_range"][0]
        progress_pct = ((points - current_min) / (next_min - current_min)) * 100
    else:
        progress_pct = 100
    
    return {
        "current_milestone": current_milestone,
        "next_milestone": next_milestone,
        "progress_percentage": progress_pct,
        "ml_engineer_recs": get_recommendations_for_level(skill_level, topic_coverage, "ml_engineer"),
        "researcher_recs": get_recommendations_for_level(skill_level, topic_coverage, "ai_researcher"),
        "focus_areas": current_milestone.get("focus_areas", []),
        "recommended_projects": current_milestone.get("recommended_projects", [])
    }
