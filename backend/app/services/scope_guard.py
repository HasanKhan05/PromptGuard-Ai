import json
import logging
import re
from dataclasses import dataclass

from openai import AsyncOpenAI

from ..config import get_settings
from .llm import extract_text_content

logger = logging.getLogger(__name__)

DEFAULT_REFUSAL_MESSAGE = (
    "I am PromptGuard Ai, a dedicated software development assistant. "
    "I can only help with programming, code review, debugging, software architecture, "
    "development tools, and related software engineering tasks. "
    "Your request appears to be outside this scope. Please provide a software-related question or coding task."
)

CLASSIFIER_SYSTEM_PROMPT = (
    "You are a strict scope classifier for a Software Development Assistant. "
    "Determine if the user's prompt is a request for software development, programming, "
    "code explanation, debugging, software architecture, dev tools, or technical computer science concepts. "
    "Software tasks about any topic or domain (e.g. building a car price scraper or healthcare database) are IN SCOPE. "
    "Pure non-technical questions (e.g. recipes, medical advice, general trivia, consumer shopping) are OUT OF SCOPE. "
    'Respond with compact JSON only: {"allowed": true} or {"allowed": false, "reason": "short explanation"}.'
)


@dataclass(frozen=True)
class ScopeDecision:
    allowed: bool
    method: str  # "deterministic_allow", "deterministic_reject", "llm_classifier"
    reason: str
    refusal_message: str | None = None


# --- Deterministic Patterns ---

CODE_SYNTAX_PATTERNS = [
    re.compile(r"```[\s\S]*?```"),  # Fenced code blocks
    re.compile(r"`[^`\n]{2,}`"),  # Inline code
    re.compile(r"\b(?:def|class|function|async\s+def|public\s+class|public\s+static\s+void)\s+\w+"),
    re.compile(r"\b(?:import\s+[\w.]+|from\s+[\w.]+\s+import|#include\s*<[\w.]+>|package\s+[\w.]+)"),
    re.compile(r"\b(?:const|let|var)\s+\w+\s*="),
    re.compile(r"\b(?:SELECT\s+.+\s+FROM|INSERT\s+INTO|CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE)\b", re.IGNORECASE),
    re.compile(r"\b(?:Traceback\s+\(most\s+recent\s+call\s+last\)|NullPointerException|TypeError:|SyntaxError:|ValueError:|KeyError:|IndexError:)", re.IGNORECASE),
    re.compile(r"\b(?:console\.log|print\(|System\.out\.println|fmt\.Print|std::cout)\b"),
    re.compile(r"\.(?:py|js|ts|tsx|jsx|rs|go|cpp|c|java|cs|php|rb|html|css|sql|sh|yaml|yml|json|toml)\b"),
]

SOFTWARE_ACTION_PATTERNS = [
    re.compile(r"\b(?:write|create|build|implement|develop|code|generate|design|setup|configure)\s+(?:a|an|the|some)?\s*(?:script|code|function|program|app|application|api|service|endpoint|database|schema|query|algorithm|class|module|interface|pipeline|scraper|crawler|parser|bot|component|server|backend|frontend|cli|webhook|microservice)\b", re.IGNORECASE),
    re.compile(r"\b(?:how\s+(?:do\s+i|to))\s+(?:code|program|build|implement|develop|debug|refactor|compile|deploy|test|parse|serialize|deserialize|mock|lint|profile|containerize|benchmark)\b", re.IGNORECASE),
    re.compile(r"\b(?:how\s+(?:do\s+i|to))\s+(?:write|create|connect|fetch|query|parse|filter|sort|map|reduce)\s+(?:a|an|the|in|with|using)?\s*(?:api|database|sql|json|csv|array|list|dict|dataframe|table|route|endpoint)\b", re.IGNORECASE),
    re.compile(r"\b(?:debug|refactor|optimize|review|analyze|explain|fix)\s+(?:this|my|the|some)?\s*(?:code|function|script|bug|error|exception|query|algorithm|class|snippet|implementation|performance|memory\s+leak|stack\s+trace)\b", re.IGNORECASE),
    re.compile(r"\b(?:unit\s+test|integration\s+test|e2e\s+test|test\s+case|pull\s+request|merge\s+conflict|git\s+commit|git\s+branch|git\s+rebase)\b", re.IGNORECASE),
]

SOFTWARE_KEYWORDS = {
    # Languages & formats
    "python", "javascript", "typescript", "rust", "golang", "go lang", "c++", "c#", "java", "kotlin",
    "swift", "ruby", "php", "scala", "haskell", "elixir", "clojure", "lua", "bash", "powershell", "sql",
    "html", "css", "sass", "scss", "graphql", "protobuf", "json", "yaml", "xml",
    # Frameworks & libraries
    "react", "nextjs", "next.js", "vue", "angular", "svelte", "django", "flask", "fastapi", "express",
    "expressjs", "express.js", "nodejs", "node.js", "spring boot", "asp.net", "laravel", "rails",
    "pandas", "numpy", "pytorch", "tensorflow", "scikit-learn", "sqlalchemy", "prisma", "tailwind",
    # Infrastructure & tools
    "docker", "dockerfile", "kubernetes", "k8s", "git", "github", "gitlab", "npm", "pip", "cargo",
    "poetry", "webpack", "vite", "nginx", "apache", "postgres", "postgresql", "mysql", "sqlite",
    "mongodb", "redis", "elasticsearch", "kafka", "rabbitmq",
    # CS / Dev concepts
    "algorithm", "data structure", "linked list", "binary tree", "binary search", "hash table", "hash map",
    "recursion", "async/await", "concurrency", "multithreading", "goroutine", "deadlock", "race condition",
    "rest api", "restful", "crud", "endpoint", "webhook", "middleware", "orm", "sdk", "cli",
    "polymorphism", "inheritance", "dependency injection", "design pattern", "microservice",
    "linter", "compiler", "interpreter", "debugger", "profiler", "regex", "regular expression",
    # Security in code / AppSec (legitimate coding context)
    "sql injection", "sqli", "cross-site scripting", "xss", "csrf", "buffer overflow", "redos",
    "input sanitization", "parameterized query", "prepared statement", "jwt", "oauth", "oauth2",
    "bcrypt", "argon2", "password hashing", "cors", "rate limiting", "vulnerability fix", "security patch",
}

OUT_OF_SCOPE_PATTERNS = [
    # Recipes & cooking
    re.compile(r"\b(?:recipe\s+for|how\s+to\s+(?:bake|cook|fry|grill|roast|boil|prepare\s+(?:food|dinner|lunch|breakfast|cake|pasta|bread|soup|curry))|ingredients\s+(?:for|in)|calories\s+in|best\s+restaurants?\s+in)\b", re.IGNORECASE),
    # Medical & health advice
    re.compile(r"\b(?:symptoms\s+of|treatment\s+for|cure\s+for|medicine\s+for|dosage\s+of|home\s+remedies\s+for|how\s+to\s+(?:cure|treat|diagnose)\s+(?:a|an|the|my)?\s*(?:headache|flu|cold|cancer|diabetes|fever|infection|pain)|side\s+effects\s+of\s+\w+)\b", re.IGNORECASE),
    # Consumer shopping & non-tech pricing
    re.compile(r"\b(?:what\s+is\s+the\s+price\s+of\s+(?:a|an)?\s*(?:toyota|honda|car|shoes|shirt|house|apartment|watch|bag|furniture|flight|ticket)|cost\s+of\s+living\s+in|best\s+car\s+to\s+buy|best\s+shoes\s+for|cheap\s+flights\s+to|hotels?\s+in)\b", re.IGNORECASE),
    # Non-technical trivia / history / geography / sports
    re.compile(r"\b(?:who\s+(?:is|was)\s+(?:the\s+president|the\s+prime\s+minister|the\s+king|the\s+queen|the\s+actor|the\s+singer|the\s+founder)\s+of|capital\s+of|population\s+of|who\s+won\s+(?:the\s+)?(?:[a-z0-9]+\s+)*(?:world\s+cup|super\s+bowl|oscars?|championship|tournament|olympics|match|game|election)|when\s+did\s+world\s+war)\b", re.IGNORECASE),
    # Creative writing (non-technical)
    re.compile(r"\b(?:write\s+(?:a|an|the|some)?\s*(?:[a-z]+\s+)?(?:poem|poetry|love\s+letter|song\s+lyrics|lyrics|bedtime\s+story|fairy\s+tale|fiction\s+story|romance\s+novel|short\s+story|novel|speech|essay))\b", re.IGNORECASE),
    # Astrology / Horoscope / Dating
    re.compile(r"\b(?:horoscope\s+for|zodiac\s+sign|relationship\s+advice|dating\s+tips|pickup\s+lines)\b", re.IGNORECASE),
    # Pure financial investment advice
    re.compile(r"\b(?:should\s+i\s+buy\s+(?:tesla|apple|bitcoin|crypto|stocks?)|stock\s+price\s+prediction|how\s+to\s+get\s+rich\s+quick)\b", re.IGNORECASE),
]


def evaluate_scope_deterministic(prompt: str) -> ScopeDecision | None:
    """
    Evaluates scope deterministically without any LLM calls.
    Returns ScopeDecision if confident, or None if genuinely ambiguous.
    """
    cleaned = prompt.strip()
    if not cleaned:
        return ScopeDecision(
            allowed=False,
            method="deterministic_reject",
            reason="Empty prompt",
            refusal_message=DEFAULT_REFUSAL_MESSAGE,
        )

    # 1. Check for concrete code syntax / blocks
    for pattern in CODE_SYNTAX_PATTERNS:
        if pattern.search(cleaned):
            return ScopeDecision(
                allowed=True,
                method="deterministic_allow",
                reason="Code syntax or code block detected",
            )

    # 2. Check for software development actions
    for pattern in SOFTWARE_ACTION_PATTERNS:
        if pattern.search(cleaned):
            return ScopeDecision(
                allowed=True,
                method="deterministic_allow",
                reason="Software development action or intent detected",
            )

    # 3. Check for specific software keywords
    lower_prompt = cleaned.lower()
    for kw in SOFTWARE_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, lower_prompt):
            return ScopeDecision(
                allowed=True,
                method="deterministic_allow",
                reason=f"Software keyword '{kw}' detected",
            )

    # 4. Check for obvious non-software out-of-scope patterns
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if pattern.search(cleaned):
            return ScopeDecision(
                allowed=False,
                method="deterministic_reject",
                reason="Out-of-scope domain pattern detected",
                refusal_message=DEFAULT_REFUSAL_MESSAGE,
            )

    # If neither clearly software nor clearly out-of-scope, return None (ambiguous)
    return None


async def classify_scope_llm(prompt: str) -> ScopeDecision:
    """
    Single compact LLM classifier call for genuinely ambiguous prompts.
    Uses ultra-low token budget (max 40 tokens) and returns structured JSON.
    """
    settings = get_settings()
    if not settings.omniroute_api_key:
        logger.warning("OmniRoute API key not set for LLM scope classifier; falling back to allow.")
        return ScopeDecision(
            allowed=True,
            method="llm_classifier",
            reason="Ambiguous prompt permitted (no classifier key)",
        )

    client = AsyncOpenAI(
        base_url=settings.omniroute_base_url,
        api_key=settings.omniroute_api_key,
    )

    truncated_prompt = prompt[:400]

    try:
        response = await client.chat.completions.create(
            model=settings.normal_assistant_model,
            messages=[
                {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify this prompt:\n{truncated_prompt}"},
            ],
            temperature=0.0,
            max_tokens=40,
        )
        raw_content = response.choices[0].message.content if response.choices else None
        content = extract_text_content(raw_content) or "{}"
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
        else:
            parsed = json.loads(content)
        allowed = bool(parsed.get("allowed", True))
        reason = parsed.get("reason", "Classified by LLM")

        return ScopeDecision(
            allowed=allowed,
            method="llm_classifier",
            reason=reason,
            refusal_message=DEFAULT_REFUSAL_MESSAGE if not allowed else None,
        )
    except Exception as exc:
        logger.warning(f"LLM scope classifier error: {exc}. Defaulting to allowed for safety.")
        return ScopeDecision(
            allowed=True,
            method="llm_classifier",
            reason=f"Classifier fallback allowed on error: {exc}",
        )


async def check_scope(prompt: str) -> ScopeDecision:
    """
    Deterministic-first scope check.
    Only falls back to 1 compact LLM call if prompt is genuinely ambiguous.
    """
    decision = evaluate_scope_deterministic(prompt)
    if decision is not None:
        return decision

    return await classify_scope_llm(prompt)
