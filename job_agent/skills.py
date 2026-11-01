"""Skill vocabulary used for matching jobs to the CV.

Add your own niche skills with EXTRA_SKILLS in .env instead of editing this list.
"""

SKILLS = [
    # languages
    "python", "java", "javascript", "typescript", "c++", "c#", "golang",
    "rust", "ruby", "php", "kotlin", "swift", "scala", "matlab", "dart", "sql",
    "bash", "html", "css",
    # web / frameworks
    "react", "next.js", "vue", "angular", "svelte", "node.js", "express.js", "nestjs",
    "django", "flask", "fastapi", "spring", "spring boot", ".net", "asp.net", "laravel",
    "rails", "flutter", "react native", "graphql", "rest api", "grpc", "tailwind",
    # data / ml
    "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow", "keras", "spark",
    "hadoop", "airflow", "dbt", "kafka", "machine learning", "deep learning", "nlp",
    "computer vision", "data analysis", "data engineering", "etl", "power bi", "tableau",
    "ms excel", "llm",
    # databases
    "postgresql", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
    "dynamodb", "cassandra", "snowflake", "bigquery", "oracle",
    # cloud / devops
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "ci/cd", "linux", "nginx", "serverless",
    "microservices", "git",
    # testing / practices
    "pytest", "jest", "selenium", "playwright", "cypress", "unit testing", "tdd",
    "agile", "scrum", "jira",
    # security / other
    "oauth", "jwt", "security", "networking", "embedded", "iot", "blockchain",
    "figma", "ui/ux",
    # languages spoken
    "english", "german", "french", "spanish", "arabic", "urdu",
]

# Other spellings that count as the same skill.
ALIASES = {
    "postgresql": ["postgres"],
    "golang": ["go lang"],
    "node.js": ["nodejs", "node js"],
    "express.js": ["expressjs"],
    "next.js": ["nextjs"],
    "vue": ["vue.js", "vuejs"],
    "rest api": ["rest apis", "restful", "rest-api"],
    "kubernetes": ["k8s"],
    "gcp": ["google cloud"],
    "ms excel": ["microsoft excel", "advanced excel"],
    "machine learning": ["ml engineer"],
    "ci/cd": ["ci / cd", "continuous integration"],
    "scikit-learn": ["sklearn"],
    "ui/ux": ["ux/ui", "ui design", "ux design"],
}
