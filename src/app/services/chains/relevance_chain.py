"""
Relevance Score Chain

Uses LangChain to analyze how well a resume matches a job description.
Returns a relevance score (0-100), matched keywords, and missing keywords.
"""

import json
import logging
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

RELEVANCE_PROMPT_TEMPLATE = """\
You are an expert resume analyst and HR consultant.

Analyze the following resume against the job description and provide a detailed relevance assessment.

## Resume:
{resume_text}

## Job Description:
{jd_text}

Your task:
1. Identify keywords and skills from the JD that appear in the resume (matched_keywords).
2. Identify important keywords and skills from the JD that are MISSING from the resume (missing_keywords).
3. Calculate a relevance score from 0 to 100 based on skill match, experience alignment, and overall fit.

Respond ONLY with a valid JSON object in this exact format (no extra text, no markdown):
{{
  "relevance_score": <integer 0-100>,
  "matched_keywords": ["keyword1", "keyword2", ...],
  "missing_keywords": ["keyword1", "keyword2", ...]
}}
"""


async def run_relevance_chain(resume_text: str, jd_text: str) -> dict:
    """
    Run the relevance scoring chain.

    Parameters
    ----------
    resume_text : str
        Extracted text content of the resume.
    jd_text : str
        Text content of the job description.

    Returns
    -------
    dict
        Contains: relevance_score (float), matched_keywords (list), missing_keywords (list).

    Raises
    ------
    ValueError
        If the LLM response cannot be parsed as valid JSON.
    """
    from ..llm_service import get_llm_with_fallback

    llm = get_llm_with_fallback()
    prompt = ChatPromptTemplate.from_template(RELEVANCE_PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()

    logger.info("Running relevance score chain...")
    raw_output = await chain.ainvoke({"resume_text": resume_text, "jd_text": jd_text})

    return _parse_json_response(raw_output, expected_keys=["relevance_score", "matched_keywords", "missing_keywords"])


def _parse_json_response(raw: str, expected_keys: list[str]) -> dict:
    """Parse and validate JSON from LLM output."""
    # Strip markdown code blocks if present
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}\nRaw output: {raw}")
        raise ValueError(f"LLM returned invalid JSON: {e}") from e

    for key in expected_keys:
        if key not in data:
            raise ValueError(f"LLM response missing required key: '{key}'. Got: {list(data.keys())}")

    return data
