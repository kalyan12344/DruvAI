# # lc/job_tools.py

# import json
# from pydantic import BaseModel, Field, ValidationError
# from langchain_core.tools import tool
# from lc.config import get_llm

# # --- Pydantic Models ---
# class SuggestRolesArgs(BaseModel):
#     resume_text: str = Field(..., description="The full text content of a user's resume.")

# class ResumeAnalysis(BaseModel):
#     suggested_roles: list[str] = Field(..., description="A list of 3-5 suggested job titles.")
#     experience_years: float = Field(..., description="The estimated years of experience as a number.")

# class ScoreJobArgs(BaseModel):
#     resume_text: str = Field(..., description="The full text of the candidate's resume.")
#     job_description_text: str = Field(..., description="The full text of the job description.")

# class JobMatchScore(BaseModel):
#     match_score: float = Field(..., description="A score from 0.0 to 1.0 indicating how well the resume matches the job description.")
#     reason: str = Field(..., description="A brief, one-sentence explanation for the score.")


# # --- Tool 1: Analyze Resume ---
# @tool(args_schema=SuggestRolesArgs)
# def analyze_resume(resume_text: str) -> ResumeAnalysis | None:
#     """
#     Analyzes resume text to extract suggested job titles and total years of experience.
#     Returns a structured object with both pieces of information.
#     """
#     print("🧠 Using LLM to perform comprehensive resume analysis...")
#     llm = get_llm()
#     # ... (prompt and the rest of the function is correct)
#     prompt = (
#         "Based on the following resume text, perform a comprehensive analysis. You must extract two pieces of information:\n"
#         "1. A list of up to 5 specific and modern job titles that are the best fit.\n"
#         "2. The candidate's total years of professional experience, calculated as a single number (e.g., 4.5, 10, 12.5).\n\n"
#         "Your answer MUST BE ONLY a single, root-level JSON object. It must have two keys:\n"
#         "1. 'suggested_roles' (a JSON list of strings)\n"
#         "2. 'experience_years' (a number)\n\n"
#         "Example of the required JSON format:\n"
#         "{\n"
#         "  \"suggested_roles\": [\"Senior Backend Engineer\", \"Cloud Infrastructure Specialist\"],\n"
#         "  \"experience_years\": 8.5\n"
#         "}\n\n"
#         f"--- Resume Text ---\n{resume_text}\n--- End Resume Text ---\n\n"
#         "JSON Response:"
#     )
#     raw_response = ""
#     try:
#         response_message = llm.invoke(prompt)
#         raw_response = response_message.content.strip()
#         json_start_index = raw_response.find('{')
#         json_end_index = raw_response.rfind('}')
#         if json_start_index == -1 or json_end_index == -1:
#             raise ValueError("Could not find a valid JSON object in the LLM response.")
#         json_str = raw_response[json_start_index : json_end_index + 1]
#         parsed_data = json.loads(json_str)
#         analysis_result = ResumeAnalysis(**parsed_data)
#         print(f"✅ LLM analysis successful: {analysis_result}")
#         return analysis_result
#     except (json.JSONDecodeError, ValidationError, ValueError) as e:
#         print(f"❌ Error during resume analysis: {e}")
#         print(f"--- Failing LLM Raw Response ---\n{raw_response}\n---")
#         return None

# # --- Tool 2: Score Job Match (Now with a docstring) ---
# @tool(args_schema=ScoreJobArgs)
# def score_job_match(resume_text: str, job_description_text: str) -> JobMatchScore | None:
#     """
#     Compares a resume to a job description and returns a match score from 0.0 to 1.0 and a reason.
#     The score should be high only if the key skills and required experience in the resume are a strong fit for the job.
#     """
#     print("🤖 Using LLM to score job match with STRICTER criteria...")
#     llm = get_llm()
#     prompt = (
#         "You are a strict technical recruiter. Analyze the provided resume and job description. Your task is to determine how well the candidate's skills and experience align with the job's *required* qualifications.\n\n"
#         "SCORING RULES:\n"
#         "- Be very critical. Do not give a high score just because the job titles are similar.\n"
#         "- The score MUST be based on the specific technologies, tools, and years of experience mentioned.\n"
#         "- If the job lists 'Basic Qualifications' or a minimum years of experience (e.g., '5+ years') that the candidate does not meet, the score cannot be higher than 0.4.\n"
#         "- If the job requires specific platforms (e.g., 'Informatica', 'Anaplan', 'Databricks') that are not on the resume, the score must be low.\n\n"
#         "Your response MUST be a single JSON object with two keys:\n"
#         "1. 'match_score': A floating-point number between 0.0 (no match) and 1.0 (perfect match).\n"
#         "2. 'reason': A concise, one-sentence explanation for your score, highlighting the key matching skills or the most significant missing qualifications.\n\n"
#         f"--- RESUME ---\n{resume_text}\n\n"
#         f"--- JOB DESCRIPTION ---\n{job_description_text}\n\n"
#         "JSON Response:"
#     )
#     raw_response = ""
#     try:
#         response_message = llm.invoke(prompt)
#         raw_response = response_message.content.strip()
#         json_start_index = raw_response.find('{')
#         json_end_index = raw_response.rfind('}')
#         if json_start_index == -1 or json_end_index == -1:
#             raise ValueError("No valid JSON object found in response.")
#         json_str = raw_response[json_start_index : json_end_index + 1]
#         parsed_data = json.loads(json_str)
#         validated_score = JobMatchScore(**parsed_data)
#         return validated_score
#     except (json.JSONDecodeError, ValidationError, ValueError) as e:
#         print(f"❌ Error scoring job match: {e}")
#         print(f"--- Failing LLM Raw Response ---\n{raw_response}\n---")
#         return None