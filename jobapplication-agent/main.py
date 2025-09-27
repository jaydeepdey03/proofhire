from fastapi import FastAPI, HTTPException, BackgroundTasks, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import httpx
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from jobsearch_tools.PDFTool import load_pdf
from pydantic import BaseModel
from typing import TypedDict, Optional, Dict, Any, List
import json
import asyncio
import logging
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import os
from fastapi import HTTPException
import httpx, os

app = FastAPI(swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}}  )
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI model
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
model = model.bind_tools(tools=[load_pdf])

# Pydantic models for API
class JobSearchRequest(BaseModel):
    candidate_id: str
    resume_path: Optional[str] = None
    resume_text: Optional[str] = None
    preferences: Dict[str, Any] = {}
    compatibility_threshold: float = 0.7

class Job(BaseModel):
    id: str
    title: str
    company: str
    description: str
    requirements: List[str]
    location: str
    salary_range: Optional[str] = None
    posted_date: str

class CandidateProfile(BaseModel):
    id: str
    name: str
    email: str
    skills: List[str]
    experience_years: int
    education: List[str]
    preferences: Dict[str, Any]

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

# State definition for LangGraph
class JobSearchState(TypedDict):
    candidate_id: str
    resume_text: Optional[str]
    candidate_profile: Optional[CandidateProfile]
    available_jobs: Optional[List[Job]]
    matched_jobs: Optional[List[MatchedJob]]
    compatibility_threshold: float
    preferences: Dict[str, Any]
    current_step: str
    error_message: Optional[str]
    applications: Optional[List[ApplicationDetails]]
    resume_path: Optional[str]

class JobMatchEvaluation(BaseModel):
    score: float
    reasons: List[str]
    improvements: List[str]

def run_with_tools(prompt: str, context_msgs: List = None):
    """Enhanced tool runner with context support"""
    msgs = context_msgs or []
    msgs.append(HumanMessage(content=prompt))
    
    print(f"\n=== Tool Runner Debug ===")
    print(f"Input prompt: {prompt}")
    
    result = model.invoke(msgs)
    # print(f"Model result type: {type(result)}")
    if hasattr(result, "tool_calls") and result.tool_calls:
        print(f"Tool calls found: {len(result.tool_calls)}")
        tc = result.tool_calls[0]
        tool_name = tc["name"]
        tool_args = tc["args"]
        
        # print(f"Tool name: {tool_name}")
        # print(f"Tool args: {tool_args}")
        
        try:
            tool_output = load_pdf.invoke(tool_args)
            # print(f"Tool output type: {type(tool_output)}")
            # print(f"Tool output: {tool_output}")
            
            msgs.append(result)
            msgs.append(ToolMessage(content=str(tool_output), tool_call_id=tc["id"]))
            
            result2 = model.invoke(msgs)
            # print(f"Final result type: {type(result2)}")
            # print(f"Final result: {result2}")
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

def load_candidate_profile(state: JobSearchState) -> JobSearchState:
    """Load candidate profile and resume"""
    try:
        # If resume_text is not provided, try to load from PDF
        if not state.get("resume_text") and state.get("resume_path"):
            prompt = f"Extract resume text from: {state['resume_path']}"
            print(f"\n=== PDF Tool Execution ===")
            print(f"Prompt: {prompt}")
            result = run_with_tools(prompt)
            print(f"Tool result type: {type(result)}")
            
            extracted_text = result.content if hasattr(result, 'content') else str(result)
            print(f"Extracted text preview: {extracted_text[:200] if extracted_text else 'None'}...")
            
            # Validate if extracted text is actually resume content
            is_valid, validation_reason = validate_resume_content(extracted_text)
            print(f"Content validation: {is_valid} - {validation_reason}")
            
            if is_valid:
                state["resume_text"] = extracted_text
                print("✅ Valid resume content - proceeding with job matching")
            else:
                # Use fallback or show warning
                state["resume_text"] = "No valid resume content provided"
                state["error_message"] = f"Invalid resume content: {validation_reason}"
                print(f"❌ Invalid resume content: {validation_reason}")
                print("Will proceed with basic profile matching only")
            
            print("=" * 30)
        
        # Mock getting candidate profile - replace with actual call
        profile = CandidateProfile(
            id=state["candidate_id"],
            name="Candidate",
            email="candidate@example.com",
            skills=["Python", "FastAPI", "AI"],
            experience_years=3,
            education=["BS Computer Science"],
            preferences=state.get("preferences", {})
        )
        
        state["candidate_profile"] = profile
        state["current_step"] = "profile_loaded"
        logger.info(f"Loaded profile for candidate: {state['candidate_id']}")
        
    except Exception as e:
        state["error_message"] = f"Error loading candidate profile: {str(e)}"
        logger.error(state["error_message"])
    
    return state

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
    return [
        Job(
            id="job1",
            title="Senior Python Developer",
            company="Tech Corp",
            description="Looking for experienced Python developer with FastAPI experience",
            requirements=["Python", "FastAPI", "5+ years experience"],
            location="Remote",
            salary_range="$90,000-$120,000",
            posted_date="2024-01-15"
        ),
        Job(
            id="job2",
            title="ML Engineer",
            company="AI Startup",
            description="Machine learning engineer for cutting-edge AI applications",
            requirements=["Python", "Machine Learning", "TensorFlow", "3+ years experience"],
            location="San Francisco",
            salary_range="$110,000-$150,000",
            posted_date="2024-01-16"
        )
    ]

async def apply_to_job(application: ApplicationDetails) -> Dict[str, Any]:
    """Mock function - replace with actual backend call"""
    logger.info(f"Applying to job {application.job_id} for candidate {application.candidate_id}")
    return {
        "application_id": f"app_{application.job_id}_{application.candidate_id}",
        "status": "submitted",
        "submitted_at": datetime.now().isoformat()
    }

# LangGraph node functions
def load_candidate_profile(state: JobSearchState) -> JobSearchState:
    """Load candidate profile and resume"""
    try:
        # If resume_text is not provided, try to load from PDF
        if not state.get("resume_text") and state.get("resume_path"):
            prompt = f"Extract resume text from: {state['resume_path']}"
            print(f"\n=== PDF Tool Execution ===")
            print(f"Prompt: {prompt}")
            result = run_with_tools(prompt)
            # print(f"Tool result type: {type(result)}")
            # if hasattr(result, 'content'):
                # print(f"Result content: {result.content[:200]}...")
            state["resume_text"] = result.content if hasattr(result, 'content') else str(result)
            # print(f"Final resume_text: {state['resume_text'][:200] if state['resume_text'] else 'None'}...")

            extracted_text = result.content if hasattr(result, 'content') else str(result)
            # print(f"Extracted text preview: {extracted_text[:200] if extracted_text else 'None'}...")
            
            # Validate if extracted text is actually resume content
            is_valid, validation_reason = validate_resume_content(extracted_text)
            # print(f"Content validation: {is_valid} - {validation_reason}")

            if is_valid:
                state["resume_text"] = extracted_text
                print("✅ Valid resume content - proceeding with job matching")
            else:
                # Use fallback or show warning
                state["resume_text"] = "No valid resume content provided"
                state["error_message"] = f"Invalid resume content: {validation_reason}"
                print(f"❌ Invalid resume content: {validation_reason}")
                print("Will proceed with basic profile matching only")
            
            print("=" * 30)

        # print(result, 'result')
        
        # Mock getting candidate profile - replace with actual call
        profile = CandidateProfile(
            id=state["candidate_id"],
            name="Candidate",
            email="candidate@example.com",
            skills=["Python", "FastAPI", "AI"],
            experience_years=3,
            education=["BS Computer Science"],
            preferences=state.get("preferences", {})
        )
        
        state["candidate_profile"] = profile
        state["current_step"] = "profile_loaded"
        logger.info(f"Loaded profile for candidate: {state['candidate_id']}")
        
    except Exception as e:
        state["error_message"] = f"Error loading candidate profile: {str(e)}"
        logger.error(state["error_message"])
    
    return state

def fetch_jobs(state: JobSearchState) -> JobSearchState:
    """Fetch available jobs from database"""
    try:
        # Mock job fetching - replace with actual database call
        jobs = [
            Job(
                id="job1",
                title="Senior Python Developer",
                company="Tech Corp",
                description="Looking for experienced Python developer with FastAPI experience",
                requirements=["Python", "FastAPI", "5+ years experience"],
                location="Remote",
                salary_range="$90,000-$120,000",
                posted_date="2024-01-15"
            ),
            Job(
                id="job2",
                title="ML Engineer",
                company="AI Startup", 
                description="Machine learning engineer for cutting-edge AI applications",
                requirements=["Python", "Machine Learning", "TensorFlow", "3+ years experience"],
                location="San Francisco",
                salary_range="$110,000-$150,000",
                posted_date="2024-01-16"
            ),
            Job(
                id="job3",
                title="Backend Developer",
                company="Web Solutions",
                description="Backend developer with experience in Node.js and databases",
                requirements=["Node.js", "SQL", "3+ years experience"],
                location="New York",
                salary_range="$80,000-$100,000",
                posted_date="2024-01-10"
            ),

            Job(
                id="job4",
                title="Data Scientist",
                company="Data Insights",
                description="Data scientist with strong statistical and machine learning skills",
                requirements=["Python", "R", "Machine Learning", "Statistics", "2+ years experience"],
                location="Remote",
                salary_range="$100,000-$130,000",
                posted_date="2024-01-12"
            )
        ]
        
        state["available_jobs"] = jobs
        state["current_step"] = "jobs_fetched"
        logger.info(f"Fetched {len(jobs)} available jobs")
        
    except Exception as e:
        state["error_message"] = f"Error fetching jobs: {str(e)}"
        logger.error(state["error_message"])
    
    return state

def match_jobs(state: JobSearchState) -> JobSearchState:
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
                    - Experience: {experience_years} years
                    - Education: {education}
                    - Resume: {resume}

                    Job Details:
                    - Title: {title}
                    - Company: {company}
                    - Description: {description}
                    - Requirements: {requirements}
                    - Location: {location}

                    Analyze the compatibility and provide a detailed assessment.
                    
                    {format_instructions}
                """)

                # Format the messages with actual data
                formatted_messages = prompt.format_messages(
                    skills=", ".join(candidate.skills),
                    experience_years=candidate.experience_years,
                    education=", ".join(candidate.education),
                    resume=resume_text[:800] if has_valid_resume else "No detailed resume available",
                    title=job.title,
                    company=job.company,
                    description=job.description,
                    requirements=", ".join(job.requirements),
                    location=job.location,
                    format_instructions=parser.get_format_instructions()
                )

                # Get AI response
                response = model.invoke(formatted_messages)
                
                print(f"\n=== AI Response for Job {job.id} ===")
                # print(f"Raw response: {response.content}")
                # print("=" * 50)

                # Parse using Pydantic
                parsed_result = parser.parse(response.content)
                
                print(f"Parsed score: {parsed_result.score}")
                print(f"Parsed reasons: {parsed_result.reasons}")
                print(f"Parsed improvements: {parsed_result.improvements}")

                # Check if job meets threshold
                if parsed_result.score >= threshold:
                    print(f"✅ Job {job.id} matches! Score: {parsed_result.score} >= {threshold}")
                    matched_jobs.append(MatchedJob(
                        job=job,
                        compatibility_score=parsed_result.score,
                        match_reasons=parsed_result.reasons,
                        suggested_improvements=parsed_result.improvements
                    ))
                else:
                    print(f"❌ Job {job.id} doesn't match. Score: {parsed_result.score} < {threshold}")

            except Exception as parse_error:
                print(f"❌ Parse error for job {job.id}: {parse_error}")
                print(f"Raw response was: {response.content if 'response' in locals() else 'No response'}")
                logger.warning(f"Could not parse AI response for job {job.id}: {parse_error}")
                
                # Fallback to basic skill matching
                try:
                    skill_overlap = len(set(candidate.skills) & set(job.requirements)) / len(job.requirements) if job.requirements else 0
                    if skill_overlap >= threshold:
                        print(f"✅ Using fallback scoring for job {job.id}: {skill_overlap}")
                        matched_jobs.append(MatchedJob(
                            job=job,
                            compatibility_score=skill_overlap,
                            match_reasons=["Basic skill overlap detected"],
                            suggested_improvements=["Enhance matching skills", "Provide more detailed resume"]
                        ))
                    else:
                        print(f"❌ Fallback scoring too low for job {job.id}: {skill_overlap}")
                except Exception as fallback_error:
                    print(f"❌ Fallback scoring failed for job {job.id}: {fallback_error}")
        
        # Sort by compatibility score
        matched_jobs.sort(key=lambda x: x.compatibility_score, reverse=True)
        
        state["matched_jobs"] = matched_jobs
        state["current_step"] = "jobs_matched"
        logger.info(f"Matched {len(matched_jobs)} jobs above threshold {threshold}")
        
    except Exception as e:
        state["error_message"] = f"Error matching jobs: {str(e)}"
        logger.error(state["error_message"])
    
    return state

def generate_applications(state: JobSearchState) -> JobSearchState:
    """Generate cover letters and prepare applications"""
    try:
        matched_jobs = state["matched_jobs"]
        candidate = state["candidate_profile"]
        applications = []
        
        for matched_job in matched_jobs:
            job = matched_job.job
            
            # Generate tailored cover letter
            prompt = f"""
            Generate a professional cover letter for this job application:
            
            Candidate: {candidate.name}
            Skills: {', '.join(candidate.skills)}
            Experience: {candidate.experience_years} years
            
            Job: {job.title} at {job.company}
            Description: {job.description}
            Requirements: {', '.join(job.requirements)}
            
            Match reasons: {', '.join(matched_job.match_reasons)}
            
            Create a concise, professional cover letter (200-300 words) highlighting relevant experience and enthusiasm.
            """
            
            result = model.invoke([HumanMessage(content=prompt)])
            cover_letter = result.content
            
            applications.append(ApplicationDetails(
                job_id=job.id,
                candidate_id=candidate.id,
                cover_letter=cover_letter
            ))
        
        print(applications, 'applications')
        state["applications"] = applications
        state["current_step"] = "applications_generated"
        logger.info(f"Generated {len(applications)} applications")
        
    except Exception as e:
        state["error_message"] = f"Error generating applications: {str(e)}"
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
                    "job_id": job.job.id,
                    "title": job.job.title,
                    "company": job.job.company,
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
            
            # Run workflow with streaming
            for step_result in app_workflow.stream(initial_state):
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
        media_type="text/plain",
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
