# # api/routes/resume.py

# import os
# import json
# from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

# from lc.job_tools import analyze_resume
# from lc.job_processor import process_and_cache_jobs

# from api.routes.utils import (
#     extract_text_from_pdf,
#     extract_text_from_docx,
#     get_resume_path,
#     UPLOAD_DIR,
#     RESUME_FILENAME_BASE,
#     ANALYSIS_FILE
# )

# router = APIRouter()

# @router.get("/status")
# async def get_resume_status():
#     return {"hasUploadedResume": get_resume_path() is not None}

# @router.post("/upload")
# async def upload_and_analyze_resume(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
#     """
#     Receives a resume, saves it, analyzes it, and triggers the job 
#     matching process to run in the background for a fast user experience.
#     """
#     content_type = file.content_type
#     file_contents = await file.read()

#     # Clear directory and save the new resume file
#     for filename in os.listdir(UPLOAD_DIR):
#         file_path = os.path.join(UPLOAD_DIR, filename)
#         if os.path.isfile(file_path):
#             os.remove(file_path)

#     if content_type == "application/pdf":
#         file_ext = ".pdf"
#     elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
#         file_ext = ".docx"
#     else:
#         raise HTTPException(status_code=400, detail="Invalid file type.")
    
#     save_path = os.path.join(UPLOAD_DIR, RESUME_FILENAME_BASE + file_ext)
#     with open(save_path, "wb") as f:
#         f.write(file_contents)
#     print(f"✅ Resume saved to: {save_path}")

#     # Extract text and perform initial AI analysis
#     if content_type == "application/pdf":
#         resume_text = extract_text_from_pdf(file_contents)
#     else:
#         resume_text = extract_text_from_docx(file_contents)

#     if not resume_text or len(resume_text) < 100:
#         raise HTTPException(status_code=400, detail="Could not extract sufficient text.")
    
#     analysis_result = analyze_resume.invoke(input={"resume_text": resume_text})
#     if not analysis_result:
#         raise HTTPException(status_code=404, detail="AI model did not return a valid analysis.")

#     # Save the analysis results to a JSON file
#     with open(ANALYSIS_FILE, 'w') as f:
#         json.dump(analysis_result.dict(), f, indent=2)
#     print(f"✅ Analysis results saved to {ANALYSIS_FILE}")

#     # --- RE-ENABLING BACKGROUND TASK ---
#     # The API will now respond instantly while the slow scraping happens behind the scenes.
#     background_tasks.add_task(process_and_cache_jobs)
#     print(" Kicking off job processing in the background...")
#     # The synchronous call is now removed/commented out.
#     # process_and_cache_jobs() 
#     # --- END OF CHANGE ---

#     # Return the successful analysis to the user immediately
#     return {
#         "message": "Successfully analyzed resume. Job matching has started in the background.",
#         "analysis": analysis_result.dict() 
#     }