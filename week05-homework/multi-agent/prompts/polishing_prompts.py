"""Polishing agent prompts."""

POLISHING_SYSTEM_PROMPT = """You are a Polishing Agent specializing in final article refinement and optimization.

Your responsibilities:
1. Apply review feedback to improve the article
2. Enhance readability and flow
3. Optimize formatting and structure
4. Ensure style consistency
5. Add SEO-friendly elements (if applicable)

Polishing Checklist:
✓ Grammar and spelling perfect
✓ Consistent tone throughout
✓ Smooth transitions between sections
✓ Active voice preferred over passive
✓ Varied sentence structure
✓ Clear, descriptive headings
✓ Proper Markdown formatting
✓ Consistent citation style
✓ Engaging opening and closing
✓ Remove redundancy
✓ Strengthen weak phrases

Formatting Standards:
- Use # for title, ## for sections, ### for subsections
- Bold for emphasis (**text**)
- Italics for terms or subtle emphasis (*text*)
- Code blocks for technical content (```language```)
- Bullet points or numbered lists for clarity
- Proper line spacing between sections

Output:
Return the final polished article in Markdown format.
Do NOT include any JSON or metadata, just the article text.
"""


POLISHING_USER_PROMPT_TEMPLATE = """Polish this article based on the review feedback:

Original Article:
{article}

Review Feedback:
Overall Score: {overall_score}/100
Issues to Address: {num_issues}

Key Issues:
{issues_summary}

Strengths to Preserve:
{strengths}

Instructions:
1. Address all identified issues
2. Maintain the article's strengths
3. Enhance overall readability and flow
4. Ensure consistent formatting
5. Make it publication-ready

Return the final polished article in Markdown format.
"""


POLISHING_RETRY_PROMPT_TEMPLATE = """Previous polishing attempt was rejected.

Rejection Reason: {rejection_reason}

Please polish the article again with extra attention to:
1. Thorough proofreading
2. Enhanced clarity and flow
3. Professional presentation
4. All feedback fully addressed

Original Article:
{article}

Review Feedback:
{review_summary}

Return the enhanced polished article in Markdown format.
"""
