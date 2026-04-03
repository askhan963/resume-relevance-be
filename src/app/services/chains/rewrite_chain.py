"""
Rewrite Chain

Uses LangChain to generate an AI-optimized version of a resume
tailored to a specific job description.
"""

import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

REWRITE_PROMPT_TEMPLATE = """\
You are an expert resume writer and career coach.

Your task is to rewrite the following resume to:
1. Naturally integrate the missing keywords from the job description.
2. Better align the experience and skills with what the job requires.
3. Improve ATS compatibility (use standard section headers, bullet points with action verbs).
4. Preserve all factual information — do NOT invent experience, skills, or credentials.
5. Keep a professional, concise tone.

## Original Resume:
{resume_text}

## Job Description:
{jd_text}

## Missing Keywords to Integrate (if applicable):
{missing_keywords}

## Additional Recommendations to Address:
{recommendations}

---
Rewrite the resume below. Output ONLY the rewritten resume text — no explanations, no commentary.
Start directly with the candidate's name or a professional summary.
"""


async def run_rewrite_chain(
    resume_text: str,
    jd_text: str,
    missing_keywords: list[str] | None = None,
    recommendations: list[str] | None = None,
) -> str:
    """
    Run the resume rewrite chain.

    Parameters
    ----------
    resume_text : str
        Original extracted resume text.
    jd_text : str
        Text content of the target job description.
    missing_keywords : list[str] | None
        Keywords identified as missing from the relevance/ATS analysis.
    recommendations : list[str] | None
        Specific improvement recommendations from prior analysis.

    Returns
    -------
    str
        The fully rewritten, AI-optimized resume text.
    """
    from ..llm_service import get_llm_with_fallback

    llm = get_llm_with_fallback()
    prompt = ChatPromptTemplate.from_template(REWRITE_PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()

    # Format lists for the prompt
    formatted_keywords = ", ".join(missing_keywords) if missing_keywords else "None identified."
    formatted_recommendations = (
        "\n".join(f"- {r}" for r in recommendations) if recommendations else "No specific recommendations."
    )

    logger.info("Running resume rewrite chain...")
    rewritten_text: str = await chain.ainvoke(
        {
            "resume_text": resume_text,
            "jd_text": jd_text,
            "missing_keywords": formatted_keywords,
            "recommendations": formatted_recommendations,
        }
    )

    if not rewritten_text.strip():
        raise ValueError("LLM returned an empty rewrite. Please try again.")

    logger.info(f"Rewrite complete. Output length: {len(rewritten_text)} characters.")
    return rewritten_text.strip()
