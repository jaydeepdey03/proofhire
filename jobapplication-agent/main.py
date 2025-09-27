from fastapi import FastAPI, HTTPException, BackgroundTasks, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
import os
import json
import asyncio
import logging
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from web3 import Web3
from jobsearch_tools.PDFTool import load_pdf
from pydantic import BaseModel
from typing import TypedDict, Optional, Dict, Any, List
from enum import Enum
from models import Job, Candidate, Application, Location, JobType, ApplicationStatus, JobStatus, Company
from contract_factory import contract_client
import os





app = FastAPI(swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}}  )
load_dotenv()

HARDCODED_PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HARDCODED_WALLET_ADDRESS = os.getenv("PUBLIC_KEY")


w3 = Web3(Web3.HTTPProvider("https://testnet.evm.nodes.onflow.org"))  # or your RPC URL


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI model
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
model = model.bind_tools(tools=[load_pdf])



# API models
class JobSearchRequest(BaseModel):
    candidate_id: str
    resume_path: Optional[str] = None
    resume_text: Optional[str] = None
    preferences: Dict[str, Any] = {}
    compatibility_threshold: float = 0.7

class MatchedJob(BaseModel):
    job: Job
    compatibility_score: float
    match_reasons: List[str]
    suggested_improvements: List[str]

class ApplicationDetails(BaseModel):
    job_id: str
    candidate_id: str
    cover_letter: str
    tailored_resume: Optional[str] = None

# For backward compatibility
class CandidateProfile(BaseModel):
    id: str
    name: str
    email: str
    skills: List[str]
    experience_years: int
    education: List[str]
    preferences: Dict[str, Any]

# State definition for LangGraph
class JobSearchState(TypedDict):
    candidate_id: str
    resume_text: Optional[str]
    candidate_profile: Optional[Candidate]
    available_jobs: Optional[List[Job]]
    matched_jobs: Optional[List[MatchedJob]]
    compatibility_threshold: float
    preferences: Dict[str, Any]
    current_step: str
    error_message: Optional[str]
    applications: Optional[List[ApplicationDetails]]
    resume_path: Optional[str]
    application_results: Optional[List[Dict[str, Any]]]  # Add this
    applications_summary: Optional[Dict[str, Any]]  # Add this

class JobMatchEvaluation(BaseModel):
    score: float
    reasons: List[str]
    improvements: List[str]


async def run_with_tools(prompt: str, context_msgs: List = None):
    """Enhanced async tool runner with context support"""
    msgs = context_msgs or []
    msgs.append(HumanMessage(content=prompt))
    
    print(f"\n=== Tool Runner Debug ===")
    print(f"Input prompt: {prompt}")
    
    # Use async invoke if available, otherwise regular invoke
    try:
        result = await model.ainvoke(msgs)
    except AttributeError:
        # Fallback to sync invoke if ainvoke not available
        result = model.invoke(msgs)
    
    if hasattr(result, "tool_calls") and result.tool_calls:
        print(f"Tool calls found: {len(result.tool_calls)}")
        tc = result.tool_calls[0]
        tool_name = tc["name"]
        tool_args = tc["args"]
        
        try:
            tool_output = load_pdf.invoke(tool_args)
            
            msgs.append(result)
            msgs.append(ToolMessage(content=str(tool_output), tool_call_id=tc["id"]))
            
            # Use async invoke again
            try:
                result2 = await model.ainvoke(msgs)
            except AttributeError:
                result2 = model.invoke(msgs)
            
            print("=" * 25)
            return result2
        except Exception as e:
            print(f"Tool execution error: {e}")
            logger.error(f"Tool execution error: {e}")
            return HumanMessage(content=f"Error executing tool: {str(e)}")
    
    print("No tool calls found")
    print("=" * 25)
    return result

def validate_resume_content(text: str) -> tuple[bool, str]:
    """Validate if extracted text is actually resume content"""
    if not text or len(text.strip()) < 50:
        return False, "Text too short or empty"
    
    # Use AI to validate resume content
    validation_prompt = f"""
    Analyze this text and determine if it appears to be resume/CV content.
    
    Text to analyze:
    {text[:1000]}...
    
    Look for indicators like:
    - Professional experience
    - Education details
    - Skills sections
    - Contact information
    - Work history
    - Career-related content
    
    Respond with: VALID: YES/NO | REASON: explanation
    """
    
    try:
        result = model.invoke([HumanMessage(content=validation_prompt)])
        response = result.content
        
        if "VALID: YES" in response:
            return True, "Valid resume content detected"
        else:
            reason = response.split("REASON:")[-1].strip() if "REASON:" in response else "Content doesn't appear to be resume-related"
            return False, reason
    except Exception as e:
        return False, f"Validation error: {str(e)}"

# async def load_candidate_profile(state: JobSearchState) -> JobSearchState:
#     """Load candidate profile and resume"""
#     try:
#         # If resume_text is not provided, try to load from PDF
#         # if not state.get("resume_text") and state.get("resume_path"):
#         #     prompt = f"Extract resume text from: {state['resume_path']}"~
#         #     print(f"\n=== PDF Tool Execution ===")
#         #     print(f"Prompt: {prompt}")
#         #     result = run_with_tools(prompt)
#         #     print(f"Tool result type: {type(result)}")
            
#         #     extracted_text = result.content if hasattr(result, 'content') else str(result)
#         #     print(f"Extracted text preview: {extracted_text[:200] if extracted_text else 'None'}...")
            
#         #     # Validate if extracted text is actually resume content
#         #     is_valid, validation_reason = validate_resume_content(extracted_text)
#         #     print(f"Content validation: {is_valid} - {validation_reason}")
            
#         #     if is_valid:
#         #         state["resume_text"] = extracted_text
#         #         print("✅ Valid resume content - proceeding with job matching")
#         #     else:
#         #         # Use fallback or show warning
#         #         state["resume_text"] = "No valid resume content provided"
#         #         state["error_message"] = f"Invalid resume content: {validation_reason}"
#         #         print(f"❌ Invalid resume content: {validation_reason}")
#         #         print("Will proceed with basic profile matching only")
            
#         #     print("=" * 30)
        
#         # Mock getting candidate profile - replace with actual call
#         # profile = CandidateProfile(
#         #     id=state["candidate_id"],
#         #     name="Candidate",
#         #     email="candidate@example.com",
#         #     skills=["Python", "FastAPI", "AI"],
#         #     experience_years=3,
#         #     education=["BS Computer Science"],
#         #     preferences=state.get("preferences", {})
#         # )

#         profile = await contract_client.get_candidate(state["candidate_id"])
#         print(profile, 'profile')
#         state["candidate_profile"] = profile
#         state["current_step"] = "profile_loaded"
#         logger.info(f"Loaded profile for candidate: {state['candidate_id']}")
        
#     except Exception as e:
#         state["error_message"] = f"Error loading candidate profile: {str(e)}"
#         logger.error(state["error_message"])
    
#     return state

# Mock functions - replace these with your actual backend calls
async def get_candidate_profile(candidate_id: str) -> CandidateProfile:
    """Mock function - replace with actual database call"""
    return CandidateProfile(
        id=candidate_id,
        name="John Doe",
        email="john.doe@example.com",
        skills=["Python", "FastAPI", "Machine Learning", "SQL"],
        experience_years=5,
        education=["BS Computer Science"],
        preferences={"remote": True, "salary_min": 80000}
    )

async def get_available_jobs() -> List[Job]:
    """Mock function - replace with actual database call"""
    return await contract_client.get_all_jobs()
    # return [
    #     Job(
    #         jobId="job1",
    #         companyId="company1",
    #         title="Senior Python Developer",
    #         description="Looking for experienced Python developer with FastAPI experience",
    #         requirements=["Python", "FastAPI", "5+ years experience"],
    #         skills=["Python", "FastAPI", "REST APIs"],
    #         location=Location.REMOTE,
    #         salaryRange=["90000", "120000"],
    #         jobType=JobType.FULLTIME,
    #         status=JobStatus.ACTIVE
    #     ),
    #     Job(
    #         jobId="job2",
    #         companyId="company2",
    #         title="ML Engineer",
    #         description="Machine learning engineer for cutting-edge AI applications",
    #         requirements=["Python", "Machine Learning", "TensorFlow", "3+ years experience"],
    #         skills=["Python", "Machine Learning", "TensorFlow", "PyTorch"],
    #         location=Location.HYBRID,
    #         salaryRange=["110000", "150000"],
    #         jobType=JobType.FULLTIME,
    #         status=JobStatus.ACTIVE
    #     )
    # ]

async def apply_to_job(application: ApplicationDetails) -> Dict[str, Any]:
    """Submit application using contract with hardcoded wallet"""
    try:
        application_id = f"app_{application.job_id}_{application.candidate_id}_{int(datetime.now().timestamp())}"
        
        success = await contract_client.submit_application(
            application_id,
            application.job_id,
            application.candidate_id,
            datetime.now().isoformat()
        )
        
        if success:
            return {
                "application_id": application_id,
                "status": "submitted",
                "submitted_at": datetime.now().isoformat(),
                "job_id": application.job_id,
                "candidate_id": application.candidate_id
            }
        else:
            return {
                "application_id": application_id,
                "status": "failed",
                "error": "Transaction failed"
            }
        
    except Exception as e:
        logger.error(f"Error applying to job: {e}")
        return {
            "application_id": f"app_{application.job_id}_{application.candidate_id}",
            "status": "failed",
            "error": str(e)
        }

# LangGraph node functions
async def load_candidate_profile(state: JobSearchState) -> JobSearchState:
    """Load candidate profile and resume"""
    try:
        # If resume_text is not provided, try to load from PDF
        if not state.get("resume_text") and state.get("resume_path"):
            prompt = f"Extract resume text from: {state['resume_path']}"
            print(f"\n=== PDF Tool Execution ===")
            print(f"Prompt: {prompt}")
            
            # NOW this is an async call
            result = await run_with_tools(prompt)
            
            extracted_text = result.content if hasattr(result, 'content') else str(result)
            
            # Validate if extracted text is actually resume content
            is_valid, validation_reason = validate_resume_content(extracted_text)

            if is_valid:
                state["resume_text"] = extracted_text
                print("✅ Valid resume content - proceeding with job matching")
            else:
                state["resume_text"] = "No valid resume content provided"
                state["error_message"] = f"Invalid resume content: {validation_reason}"
                print(f"❌ Invalid resume content: {validation_reason}")
                print("Will proceed with basic profile matching only")
            
            print("=" * 30)

        profile = await contract_client.get_candidate(state["candidate_id"])
        print(profile, 'profile')
        
        state["candidate_profile"] = profile
        state["current_step"] = "profile_loaded"
        logger.info(f"Loaded profile for candidate: {state['candidate_id']}")
        
    except Exception as e:
        state["error_message"] = f"Error loading candidate profile: {str(e)}"
        logger.error(state["error_message"])
    
    return state

async def fetch_jobs(state: JobSearchState) -> JobSearchState:
    """Fetch available jobs from database"""
    try:
        jobs = await contract_client.get_all_jobs()
        print(jobs, 'fucku')
        state["available_jobs"] = jobs
        state["current_step"] = "jobs_fetched"
        logger.info(f"Fetched {len(jobs)} available jobs")
    except Exception as e:
        state["error_message"] = f"Error fetching jobs: {str(e)}"
        logger.error(state["error_message"])
    return state

async def match_jobs(state: JobSearchState) -> JobSearchState:
    """Use AI to match jobs with candidate profile"""
    try:
        candidate = state["candidate_profile"]
        jobs = state["available_jobs"]
        threshold = state["compatibility_threshold"]
        resume_text = state.get("resume_text", "")
        
        matched_jobs = []

        print("Candidate Profile:", candidate)
        print("Number of Available Jobs:", len(jobs) if jobs else 0)
        print(f"Resume text length: {len(resume_text) if resume_text else 0}")

        has_valid_resume = resume_text and resume_text != "No valid resume content provided"
        print(f"Has valid resume content: {has_valid_resume}")
        
        # Create parser outside the loop
        parser = PydanticOutputParser(pydantic_object=JobMatchEvaluation)
        
        for job in jobs:
            try:
                # Create the prompt template with proper formatting
                prompt = ChatPromptTemplate.from_template("""
                    Analyze job compatibility between candidate and job:

                    Candidate Profile:
                    - Skills: {skills}
                    - Education: {education}
                    - Resume: {resume}

                    Job Details:
                    - Title: {title}
                    - Company ID: {companyId}
                    - Description: {description}
                    - Requirements: {requirements}
                    - Location: {location}
                    - Job Type: {jobType}

                    Analyze the compatibility and provide a detailed assessment.
                    
                    {format_instructions}
                """)

                # Format the messages with actual data
                formatted_messages = prompt.format_messages(
                    skills=", ".join(candidate.skills),
                    education=", ".join(candidate.education),
                    resume=resume_text[:800] if has_valid_resume else "No detailed resume available",
                    title=job.title,
                    companyId=job.companyId,
                    description=job.description,
                    requirements=", ".join(job.requirements),
                    location=job.location.value,
                    jobType=job.jobType.value,
                    format_instructions=parser.get_format_instructions()
                )

                # Get AI response
                response = model.invoke(formatted_messages)
                
                print(f"\n=== AI Response for Job {job.jobId} ===")
                # print(f"Raw response: {response.content}")
                # print("=" * 50)

                # Parse using Pydantic
                parsed_result = parser.parse(response.content)
                
                print(f"Parsed score: {parsed_result.score}")
                print(f"Parsed reasons: {parsed_result.reasons}")
                print(f"Parsed improvements: {parsed_result.improvements}")

                # Check if job meets threshold
                if parsed_result.score >= threshold:
                    print(f"✅ Job {job.jobId} matches! Score: {parsed_result.score} >= {threshold}")
                    matched_jobs.append(MatchedJob(
                        job=job,
                        compatibility_score=parsed_result.score,
                        match_reasons=parsed_result.reasons,
                        suggested_improvements=parsed_result.improvements
                    ))
                else:
                    print(f"❌ Job {job.jobId} doesn't match. Score: {parsed_result.score} < {threshold}")

            except Exception as parse_error:
                print(f"❌ Parse error for job {job.jobId}: {parse_error}")
                print(f"Raw response was: {response.content if 'response' in locals() else 'No response'}")
                logger.warning(f"Could not parse AI response for job {job.jobId}: {parse_error}")
                
                # Fallback to basic skill matching
                try:
                    skill_overlap = len(set(candidate.skills) & set(job.requirements)) / len(job.requirements) if job.requirements else 0
                    if skill_overlap >= threshold:
                        print(f"✅ Using fallback scoring for job {job.jobId}: {skill_overlap}")
                        matched_jobs.append(MatchedJob(
                            job=job,
                            compatibility_score=skill_overlap,
                            match_reasons=["Basic skill overlap detected"],
                            suggested_improvements=["Enhance matching skills", "Provide more detailed resume"]
                        ))
                    else:
                        print(f"❌ Fallback scoring too low for job {job.jobId}: {skill_overlap}")
                except Exception as fallback_error:
                    print(f"❌ Fallback scoring failed for job {job.jobId}: {fallback_error}")
        
        # Sort by compatibility score
        matched_jobs.sort(key=lambda x: x.compatibility_score, reverse=True)
        
        state["matched_jobs"] = matched_jobs
        state["current_step"] = "jobs_matched"
        logger.info(f"Matched {len(matched_jobs)} jobs above threshold {threshold}")
        
    except Exception as e:
        state["error_message"] = f"Error matching jobs: {str(e)}"
        logger.error(state["error_message"])
    
    return state

async def generate_applications(state: JobSearchState) -> JobSearchState:
    """Prepare applications without cover letters"""
    try:
        matched_jobs = state["matched_jobs"]
        candidate = state["candidate_profile"]
        applications = []
        
        logger.info(f"Preparing applications for {len(matched_jobs)} matched jobs")
        
        for matched_job in matched_jobs:
            job = matched_job.job
            
            # Create simple application without cover letter
            applications.append(ApplicationDetails(
                job_id=job.jobId,
                candidate_id=candidate.candidateId,
                cover_letter=""  # Empty cover letter as we don't need it
            ))
        
        state["applications"] = applications
        state["current_step"] = "applications_generated"
        logger.info(f"Prepared {len(applications)} applications")
        
    except Exception as e:
        state["error_message"] = f"Error generating applications: {str(e)}"
        logger.error(state["error_message"])
    
    return state

async def apply_to_jobs_node(state: JobSearchState) -> JobSearchState:
    """Apply to all matched jobs using the smart contract"""
    try:
        applications = state.get("applications", [])
        if not applications:
            state["error_message"] = "No applications to submit"
            return state
        
        application_results = []
        successful_applications = 0
        failed_applications = 0
        
        logger.info(f"Starting to apply to {len(applications)} jobs")
        
        for i, application in enumerate(applications):
            try:
                logger.info(f"Applying to job {i+1}/{len(applications)}: {application.job_id}")
                
                # Generate unique application ID
                application_id = f"app_{application.job_id}_{application.candidate_id}_{int(datetime.now().timestamp())}_{i}"
                
                # Submit application to smart contract
                success = await contract_client.submit_application(
                    application_id,
                    application.job_id,
                    application.candidate_id,
                    datetime.now().isoformat()
                )
                
                if success:
                    successful_applications += 1
                    result = {
                        "application_id": application_id,
                        "job_id": application.job_id,
                        "status": "submitted",
                        "submitted_at": datetime.now().isoformat(),
                        "message": "Application submitted successfully to blockchain"
                    }
                    logger.info(f"✅ Application {application_id} submitted successfully")
                else:
                    failed_applications += 1
                    result = {
                        "application_id": application_id,
                        "job_id": application.job_id,
                        "status": "failed",
                        "submitted_at": datetime.now().isoformat(),
                        "error": "Smart contract transaction failed"
                    }
                    logger.error(f"❌ Application {application_id} failed")
                
                application_results.append(result)
                
                # Add small delay between applications
                await asyncio.sleep(1)
                
            except Exception as app_error:
                failed_applications += 1
                error_result = {
                    "application_id": f"app_{application.job_id}_{application.candidate_id}_error",
                    "job_id": application.job_id,
                    "status": "failed",
                    "submitted_at": datetime.now().isoformat(),
                    "error": str(app_error)
                }
                application_results.append(error_result)
                logger.error(f"❌ Error applying to job {application.job_id}: {app_error}")
        
        # Update state with results
        state["application_results"] = application_results
        state["applications_summary"] = {
            "total": len(applications),
            "successful": successful_applications,
            "failed": failed_applications,
            "success_rate": successful_applications / len(applications) if applications else 0,
            "submission_timestamp": datetime.now().isoformat()
        }
        state["current_step"] = "applications_submitted"
        
        logger.info(f"Application process completed: {successful_applications} successful, {failed_applications} failed")
        
    except Exception as e:
        state["error_message"] = f"Error in application process: {str(e)}"
        logger.error(state["error_message"])
    
    return state


def should_continue(state: JobSearchState) -> str:
    """Determine next step in workflow"""
    if state.get("error_message"):
        return END

    current_step = state.get("current_step", "")

    if current_step == "profile_loaded":
        return "fetch_jobs"
    elif current_step == "jobs_fetched":
        return "match_jobs"
    elif current_step == "jobs_matched":
        return "generate_applications"
    elif current_step == "applications_generated":
        return "apply_jobs"   # <-- FIXED: was "" before
    elif current_step == "applications_submitted":
        return END
    else:
        return "load_profile"

# Build the workflow graph
workflow = StateGraph(JobSearchState)

# Add nodes
workflow.add_node("load_profile", load_candidate_profile)
workflow.add_node("fetch_jobs", fetch_jobs)
workflow.add_node("match_jobs", match_jobs)
workflow.add_node("generate_applications", generate_applications)
workflow.add_node("apply_jobs", apply_to_jobs_node)

# Add edges
workflow.set_entry_point("load_profile")
workflow.add_conditional_edges(
    "load_profile",
    should_continue,
    {
        "fetch_jobs": "fetch_jobs",
        END: END
    }
)
workflow.add_conditional_edges(
    "fetch_jobs",
    should_continue,
    {
        "match_jobs": "match_jobs",
        END: END
    }
)
workflow.add_conditional_edges(
    "match_jobs",
    should_continue,
    {
        "generate_applications": "generate_applications",
        END: END
    }
)
workflow.add_conditional_edges(
    "generate_applications",
    should_continue,
    {
        "apply_jobs": "apply_jobs",  # FIXED: Make sure this edge exists
        END: END
    }
)
workflow.add_conditional_edges(
    "apply_jobs",
    should_continue,
    {
        END: END
    }
)

# Compile the workflow
app_workflow = workflow.compile()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Job Platform AI Agent API", "version": "1.0.0"}

@app.post("/search-jobs")
async def search_jobs(request: JobSearchRequest):
    """Main endpoint to search and match jobs for a candidate"""
    try:
        # Initialize state
        initial_state = JobSearchState(
            candidate_id=request.candidate_id,
            resume_text=request.resume_text,
            compatibility_threshold=request.compatibility_threshold,
            preferences=request.preferences,
            current_step="start"
        )
        
        # Run the workflow
        result = app_workflow.invoke(initial_state)
        
        if result.get("error_message"):
            raise HTTPException(status_code=400, detail=result["error_message"])
        
        return {
            "candidate_id": result["candidate_id"],
            "matched_jobs_count": len(result.get("matched_jobs", [])),
            "matched_jobs": [
                {
                    "job_id": job.job.jobId,
                    "title": job.job.title,
                    "company_id": job.job.companyId,
                    "description": job.job.description,
                    "location": job.job.location.value,
                    "job_type": job.job.jobType.value,
                    "salary_range": job.job.salaryRange,
                    "compatibility_score": job.compatibility_score,
                    "match_reasons": job.match_reasons,
                    "suggested_improvements": job.suggested_improvements
                }
                for job in result.get("matched_jobs", [])
            ],
            "applications_ready": len(result.get("applications", [])),
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error in job search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search-jobs/{candidate_id}/stream")
async def stream_job_search(
    candidate_id: str = Path(..., description="The ID of the candidate to search jobs for"),
    compatibility_threshold: float = Query(0.7, description="Minimum compatibility score for job matching", ge=0.0, le=1.0)
):
    """Stream job search progress to frontend"""
    
    async def generate_stream():
        try:
            initial_state = JobSearchState(
                candidate_id=candidate_id,
                compatibility_threshold=compatibility_threshold,
                preferences={},
                current_step="start",
                resume_path="/Users/jaydeepdey/Desktop/doc/Resume_Jaydeep_2024.pdf"
            )
            
            # Stream each step
            yield f"data: {json.dumps({'step': 'started', 'message': 'Starting job search'})}\n\n"
            
            # FIXED: Use async for loop with astream
            async for step_result in app_workflow.astream(initial_state):
                step_name = list(step_result.keys())[0]
                state = step_result[step_name]
                
                event_data = {
                    'step': step_name,
                    'current_step': state.get('current_step', ''),
                    'message': f'Completed {step_name}'
                }
                
                if step_name == 'match_jobs' and state.get('matched_jobs'):
                    event_data['matched_count'] = len(state['matched_jobs'])
                
                yield f"data: {json.dumps(event_data)}\n\n"
            
            yield f"data: {json.dumps({'step': 'completed', 'message': 'Job search completed'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.post("/apply-jobs/{candidate_id}")
async def apply_to_jobs(
    candidate_id: str = Path(..., description="The ID of the candidate to apply jobs for"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Apply to all matched jobs for a candidate"""
    try:
        # This would typically fetch the applications from the previous search
        # For now, we'll mock this
        applications = [
            ApplicationDetails(
                job_id="job1",
                candidate_id=candidate_id,
                cover_letter="Mock cover letter"
            )
        ]
        
        application_results = []
        for app in applications:
            # Add background task for actual application submission
            background_tasks.add_task(apply_to_job, app)
            application_results.append({
                "job_id": app.job_id,
                "status": "submitted",
                "message": "Application submitted successfully"
            })
        
        return {
            "candidate_id": candidate_id,
            "applications_submitted": len(application_results),
            "results": application_results
        }
        
    except Exception as e:
        logger.error(f"Error applying to jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/candidate/{candidate_id}/profile")
async def get_candidate_profile_endpoint(
    candidate_id: str = Path(..., description="The ID of the candidate to get profile for")
):
    """Get candidate profile"""
    try:
        profile = await get_candidate_profile(candidate_id)
        return profile
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Candidate not found: {str(e)}")

@app.get("/jobs")
async def get_jobs():
    """Get all available jobs"""
    try:
        jobs = await get_available_jobs()
        print(jobs, 'jobs')
        return {"jobs": jobs, "count": len(jobs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")


# Request body
class MetadataUpdateRequest(BaseModel):
    user_id: str
    custom_metadata: Optional[Dict[str, Any]] = None



@app.post("/set-user-metadata")
async def set_user_metadata(req: MetadataUpdateRequest):
    privy_app_id = os.getenv("PRIVY_APP_ID")
    privy_app_secret = os.getenv("PRIVY_APP_SECRET")
    if not privy_app_id or not privy_app_secret:
        raise HTTPException(status_code=500, detail="Privy credentials not set")

    url = f"https://api.privy.io/v1/users/{req.user_id}/custom_metadata"
    headers = {
        "Content-Type": "application/json",
        "privy-app-id": privy_app_id,
    }
    body = {"custom_metadata": req.custom_metadata}

    try:
        async with httpx.AsyncClient(auth=httpx.BasicAuth(privy_app_id, privy_app_secret)) as client:
            response = await client.post(url, headers=headers, json=body)

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Privy API error: {response.text}",
            )

        return response.json()

    except httpx.RequestError as e:
        print("Request error:", e)
        raise HTTPException(status_code=502, detail=f"Request error: {str(e)}")
    except Exception as e:
        print("Unexpected error:", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

