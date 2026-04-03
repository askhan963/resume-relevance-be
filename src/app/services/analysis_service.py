"""
Analysis Service

Orchestrates the full resume analysis pipeline:
1. Runs the Relevance Score Chain
2. Runs the ATS Score Chain
3. Merges results into a unified AnalysisResult

Both chains run concurrently via asyncio.gather for performance.
"""

import asyncio
import logging

from ..schemas.analysis import AnalysisResult
from .chains.ats_chain import run_ats_chain
from .chains.relevance_chain import run_relevance_chain
from .chains.rewrite_chain import run_rewrite_chain

logger = logging.getLogger(__name__)


async def analyze_resume(resume_text: str, jd_text: str) -> AnalysisResult:
    """
    Run all analysis chains concurrently and merge results.

    Parameters
    ----------
    resume_text : str
        Extracted text content from the uploaded resume.
    jd_text : str
        Full text of the job description.

    Returns
    -------
    AnalysisResult
        Unified result containing relevance score, ATS score,
        matched/missing keywords, and recommendations.
    """
    logger.info("Starting concurrent analysis (relevance + ATS)...")

    # Run both chains concurrently
    relevance_result, ats_result = await asyncio.gather(
        run_relevance_chain(resume_text, jd_text),
        run_ats_chain(resume_text, jd_text),
    )

    # Merge and deduplicate missing_keywords from both chains
    all_missing = list(
        dict.fromkeys(
            relevance_result.get("missing_keywords", []) + ats_result.get("missing_keywords", [])
        )
    )

    return AnalysisResult(
        relevance_score=float(relevance_result.get("relevance_score", 0)),
        ats_score=float(ats_result.get("ats_score", 0)),
        matched_keywords=relevance_result.get("matched_keywords", []),
        missing_keywords=all_missing,
        recommendations=ats_result.get("recommendations", []),
    )


async def rewrite_resume(
    resume_text: str,
    jd_text: str,
    missing_keywords: list[str] | None = None,
    recommendations: list[str] | None = None,
) -> str:
    """
    Generate an AI-rewritten resume optimized for the target JD.

    Parameters
    ----------
    resume_text : str
        Original resume text.
    jd_text : str
        Target job description text.
    missing_keywords : list[str] | None
        Keywords from prior analysis to incorporate.
    recommendations : list[str] | None
        Improvement recommendations from prior analysis.

    Returns
    -------
    str
        AI-rewritten resume as plain text.
    """
    logger.info("Starting resume rewrite...")
    return await run_rewrite_chain(
        resume_text=resume_text,
        jd_text=jd_text,
        missing_keywords=missing_keywords,
        recommendations=recommendations,
    )
