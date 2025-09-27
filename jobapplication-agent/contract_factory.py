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
        """Submit an application to the smart contract using hardcoded wallet"""
        try:
            # Get hardcoded wallet from environment variables
            private_key = os.getenv("PRIVATE_KEY")
            if not private_key:
                logger.error("PRIVATE_KEY not found in environment variables")
                return False
            
            # Ensure proper private key format
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            private_key = '0x' + private_key
            
            # Create account from private key
            account = Account.from_key(private_key)
            logger.info(f"Using wallet address: {account.address}")
            
            # Check if wallet has sufficient balance
            balance = self.w3.eth.get_balance(account.address)
            balance_in_flow = self.w3.from_wei(balance, 'ether')
            logger.info(f"Wallet balance: {balance_in_flow} FLOW")
            
            if balance == 0:
                logger.error("Wallet has no balance for gas fees")
                return False
            
            # Build the transaction for submitApplication function
            function_call = self.contract.functions.submitApplication(
                application_id,    # _applicationId
                job_id,           # _jobId  
                candidate_id,     # _candidateId
                application_date  # _applicationDate
            )
            
            # Get current nonce
            nonce = self.w3.eth.get_transaction_count(account.address)
            logger.info(f"Current nonce: {nonce}")
            
            # Estimate gas
            try:
                gas_estimate = function_call.estimate_gas({'from': account.address})
                logger.info(f"Estimated gas: {gas_estimate}")
            except Exception as gas_error:
                logger.error(f"Gas estimation failed: {gas_error}")
                # Use a reasonable default if estimation fails
                gas_estimate = 300000
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = self.w3.from_wei(gas_price, 'gwei')
            logger.info(f"Gas price: {gas_price_gwei} gwei")
            
            # Calculate transaction cost
            tx_cost = gas_estimate * gas_price
            tx_cost_flow = self.w3.from_wei(tx_cost, 'ether')
            
            if balance < tx_cost:
                logger.error(f"Insufficient balance for transaction. Need: {tx_cost_flow} FLOW, Have: {balance_in_flow} FLOW")
                return False
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_estimate + 50000,  # Add buffer to gas estimate
                'gasPrice': gas_price,
            })
            
            logger.info(f"Transaction built - Gas: {transaction['gas']}, Gas Price: {gas_price_gwei} gwei")
            logger.info(f"Submitting application: {application_id} for job: {job_id} by candidate: {candidate_id}")
            
            # Sign the transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=private_key)
            
            # Send the transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"Transaction sent with hash: {tx_hash_hex}")
            
            # Wait for transaction confirmation
            try:
                logger.info("Waiting for transaction confirmation...")
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                
                if receipt.status == 1:
                    logger.info(f"✅ Application submitted successfully!")
                    logger.info(f"   Application ID: {application_id}")
                    logger.info(f"   Job ID: {job_id}")
                    logger.info(f"   Candidate ID: {candidate_id}")
                    logger.info(f"   Block: {receipt.blockNumber}")
                    logger.info(f"   Gas used: {receipt.gasUsed}")
                    logger.info(f"   Transaction hash: {tx_hash_hex}")
                    
                    # Check for events (optional)
                    try:
                        # Look for ApplicationSubmitted event
                        events = self.contract.events.ApplicationSubmitted().processReceipt(receipt)
                        if events:
                            logger.info(f"   Event emitted: ApplicationSubmitted")
                            for event in events:
                                logger.info(f"   Event args: {event.args}")
                    except Exception as event_error:
                        logger.warning(f"Could not process events: {event_error}")
                    
                    return True
                else:
                    logger.error(f"❌ Transaction failed with status: {receipt.status}")
                    logger.error(f"   Transaction hash: {tx_hash_hex}")
                    return False
                    
            except Exception as receipt_error:
                logger.error(f"Error waiting for transaction receipt: {receipt_error}")
                logger.error(f"Transaction hash: {tx_hash_hex} (check manually on blockchain explorer)")
                # Transaction might still be pending, but we'll consider it failed for now
                return False
                
        except ValueError as ve:
            if "insufficient funds" in str(ve).lower():
                logger.error(f"Insufficient funds for transaction: {ve}")
            else:
                logger.error(f"Value error submitting application: {ve}")
            return False
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False
# Global contract client instance
contract_client = ContractClient()