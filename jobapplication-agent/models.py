from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

# Enums to match Solidity contract
class Location(str, Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"

class JobType(str, Enum):
    FULLTIME = "FULLTIME"
    PARTTIME = "PARTTIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"
    FREELANCE = "FREELANCE"

class ApplicationStatus(str, Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class JobStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

# Pydantic models matching Solidity structs
class Candidate(BaseModel):
    candidateId: str
    name: str
    description: List[str]
    contacts: List[str]
    education: List[str]
    skills: List[str]
    resumePath: List[str]
    profileScore: str

class Company(BaseModel):
    companyId: str
    image: str
    name: str
    contacts: List[str]
    description: str
    misc: List[str]
    companyScore: str

class Job(BaseModel):
    jobId: str
    companyId: str
    title: str
    description: str
    requirements: List[str]
    skills: List[str]
    location: Location
    salaryRange: List[str]
    jobType: JobType
    status: JobStatus

class Application(BaseModel):
    applicationId: str
    jobId: str
    candidateId: str
    applicationDate: str
    status: ApplicationStatus