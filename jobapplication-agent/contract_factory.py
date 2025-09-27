import os
from typing import List, Optional, Dict, Any
from web3 import Web3
from eth_account import Account
import json
import logging
from models import Job, Candidate, Application, Location, JobType, ApplicationStatus, JobStatus

logger = logging.getLogger(__name__)

# Contract ABI - you'll need to copy this from your client/src/lib/contractAbi.ts
# Option 1: Load from a JSON file (recommended)
with open('contract_abi.json', 'r') as f:
    CONTRACT_ABI = json.load(f)

# Option 2: Load from environment variable
# CONTRACT_ABI = json.loads(os.getenv('CONTRACT_ABI', '[]'))

# Option 3: Import from a separate Python module
# Create a file called contract_abi.py and put:
# CONTRACT_ABI = [your_abi_here]
# Then import it:
# from contract_abi import CONTRACT_ABI

class ContractClient:
    def __init__(self):
        # Use Flow Testnet RPC (from your frontend config)
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("FLOW_TESTNET_RPC", "https://testnet.evm.nodes.onflow.org")))
        
        # Contract address from your frontend
        self.contract_address = os.getenv("CONTRACT_ADDRESS", "0x519a9057Bfe3e6bab6EDb7128b7Dba44d2adC083")
        
        # Create contract instance
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=CONTRACT_ABI
        )
        
        logger.info(f"Connected to contract at {self.contract_address}")
    
    def _map_location(self, location_enum: int) -> Location:
        """Map contract location enum to Location enum"""
        location_map = {0: Location.REMOTE, 1: Location.HYBRID, 2: Location.ONSITE}
        return location_map.get(location_enum, Location.REMOTE)
    
    def _map_job_type(self, job_type_enum: int) -> JobType:
        """Map contract job type enum to JobType enum"""
        job_type_map = {
            0: JobType.FULLTIME,
            1: JobType.PARTTIME, 
            2: JobType.CONTRACT,
            3: JobType.INTERNSHIP,
            4: JobType.FREELANCE
        }
        return job_type_map.get(job_type_enum, JobType.FULLTIME)
    
    def _map_job_status(self, status_enum: int) -> JobStatus:
        """Map contract job status enum to JobStatus enum"""
        status_map = {0: JobStatus.ACTIVE, 1: JobStatus.INACTIVE}
        return status_map.get(status_enum, JobStatus.ACTIVE)
    
    def _map_application_status(self, status_enum: int) -> ApplicationStatus:
        """Map contract application status enum to ApplicationStatus enum"""
        status_map = {
            0: ApplicationStatus.PENDING,
            1: ApplicationStatus.REVIEWED,
            2: ApplicationStatus.ACCEPTED,
            3: ApplicationStatus.REJECTED
        }
        return status_map.get(status_enum, ApplicationStatus.PENDING)
    
    async def get_all_jobs(self, filters: Dict[str, Any] = None) -> List[Job]:
        """Fetch all jobs from the smart contract"""
        try:
            # Call the smart contract
            print(self.contract.functions)
            jobs_data = self.contract.functions.getAllJobs().call()
            
            jobs = []
            for job_tuple in jobs_data:
                job = Job(
                    jobId=job_tuple[0],
                    companyId=job_tuple[1], 
                    title=job_tuple[2],
                    description=job_tuple[3],
                    requirements=list(job_tuple[4]),
                    skills=list(job_tuple[5]),
                    location=self._map_location(job_tuple[6]),
                    salaryRange=list(job_tuple[7]),
                    jobType=self._map_job_type(job_tuple[8]),
                    status=self._map_job_status(job_tuple[9])
                )
                
                # Apply filters if provided
                if filters:
                    if filters.get("location") and job.location.value.lower() != filters["location"].lower():
                        continue
                    if filters.get("job_type") and job.jobType.value.lower() != filters["job_type"].lower():
                        continue
                    if filters.get("exclude_company") and job.companyId == filters["exclude_company"]:
                        continue
                
                jobs.append(job)
            
            logger.info(f"Fetched {len(jobs)} jobs from contract")
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching jobs from contract: {e}")
            return []
    
    async def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Fetch candidate data from the smart contract"""
        try:
            candidate_data = self.contract.functions.getCandidate(candidate_id).call()
            
            candidate = Candidate(
                candidateId=candidate_data[0],
                name=candidate_data[1],
                description=list(candidate_data[2]),
                contacts=list(candidate_data[3]),
                education=list(candidate_data[4]),
                skills=list(candidate_data[5]),
                resumePath=list(candidate_data[6]),
                profileScore=candidate_data[7]
            )
            
            logger.info(f"Fetched candidate {candidate_id} from contract")
            return candidate
            
        except Exception as e:
            logger.error(f"Error fetching candidate {candidate_id} from contract: {e}")
            return None
    
    async def get_applications_for_candidate(self, candidate_id: str) -> List[Application]:
        """Fetch all applications for a specific candidate"""
        try:
            all_applications = self.contract.functions.getAllApplications().call()
            
            applications = []
            for app_tuple in all_applications:
                if app_tuple[2] == candidate_id:  # candidateId matches
                    application = Application(
                        applicationId=app_tuple[0],
                        jobId=app_tuple[1],
                        candidateId=app_tuple[2],
                        applicationDate=app_tuple[3],
                        status=self._map_application_status(app_tuple[4])
                    )
                    applications.append(application)
            
            logger.info(f"Fetched {len(applications)} applications for candidate {candidate_id}")
            return applications
            
        except Exception as e:
            logger.error(f"Error fetching applications for candidate {candidate_id}: {e}")
            return []
    
    async def submit_application(self, application_id: str, job_id: str, candidate_id: str, application_date: str) -> bool:
        """Submit an application to the smart contract"""
        try:
            # This would require a wallet with gas to submit transactions
            # For read-only operations, we'll just log this for now
            logger.info(f"Would submit application {application_id} for job {job_id} by candidate {candidate_id}")
            
            # In a real implementation, you'd need:
            # 1. A funded wallet/account
            # 2. Gas estimation
            # 3. Transaction signing and submission
            
            return True
            
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False

    async def get_all_jobs(self) -> List[Job]:
        """Fetch all jobs from the smart contract"""
        try:
            # Call the smart contract
            jobs_data = self.contract.functions.getAllJobs().call()
            
            jobs = []
            for job_tuple in jobs_data:
                job = Job(
                    jobId=job_tuple[0],
                    companyId=job_tuple[1], 
                    title=job_tuple[2],
                    description=job_tuple[3],
                    requirements=list(job_tuple[4]),
                    skills=list(job_tuple[5]),
                    location=self._map_location(job_tuple[6]),
                    salaryRange=list(job_tuple[7]),
                    jobType=self._map_job_type(job_tuple[8]),
                    status=self._map_job_status(job_tuple[9])
                )
                
                jobs.append(job)
            
            logger.info(f"Fetched {len(jobs)} jobs from contract")
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching jobs from contract: {e}")
            return []

# Global contract client instance
contract_client = ContractClient()