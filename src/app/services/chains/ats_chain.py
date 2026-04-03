"""
ATS Score Chain

Analyzes resume ATS (Applicant Tracking System) friendliness against a job description.
Returns an ATS score (0-100) and specific ATS optimization recommendations.
"""

import json
import logging
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

ATS_PROMPT_TEMPLATE = """\
You are an ATS (Applicant Tracking System) expert.

Evaluate the following resume for ATS compatibility against the provided job description.
Focus on: keyword density, formatting, section headers, contact info completeness, and quantifiable achievements.

## Resume:
{resume_text}

## Job Description:
{jd_text}

ATS Score Guidelines:
- 90-100: Excellent — highly optimized, likely to pass most ATS filters
- 70-89: Good — minor improvements needed
- 50-69: Average — significant gaps in keyword alignment or formatting
- 0-49: Poor — major ATS compatibility issues

Your task:
1. Calculate an ATS score from 0 to 100.
2. Identify the top missing keywords that ATS scanners will look for.
3. Provide 3-6 specific, actionable recommendations to improve ATS compatibility.

Respond ONLY with a valid JSON object in this exact format (no extra text, no markdown):
{{
  "ats_score": <integer 0-100>,
  "missing_keywords": ["keyword1", "keyword2", ...],
  "recommendations": [
    "Recommendation 1",
    "Recommendation 2",
    ...
  ]
}}
"""


async def run_ats_chain(resume_text: str, jd_text: str) -> dict:
    """
    Run the ATS scoring chain.

    Parameters
    ----------
    resume_text : str
        Extracted text content of the resume.
    jd_text : str
        Text content of the job description.

    Returns
    -------
    dict
        Contains: ats_score (float), missing_keywords (list), recommendations (list).

    Raises
    ------
    ValueError
        If the LLM response cannot be parsed as valid JSON.
    """
    from ..llm_service import get_llm_with_fallback

    llm = get_llm_with_fallback()
    prompt = ChatPromptTemplate.from_template(ATS_PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()

    logger.info("Running ATS score chain...")
    raw_output = await chain.ainvoke({"resume_text": resume_text, "jd_text": jd_text})

    return _parse_json_response(raw_output, expected_keys=["ats_score", "missing_keywords", "recommendations"])


def _parse_json_response(raw: str, expected_keys: list[str]) -> dict:
    """Parse and validate JSON from LLM output."""
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
