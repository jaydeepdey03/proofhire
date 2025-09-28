import React from "react";
import {
  Calendar,
  MapPin,
  FileText,
  Check,
  X,
  Upload,
  Eye,
} from "lucide-react";
import { type Application } from "@/types/index";

interface ApplicationCardProps {
  application: Application[];
  userRole: "candidate" | "company";
  onStatusChange: (id: string, status: "approved" | "rejected") => void;
  onFileUpload: (id: string, file: File) => void;
  onVerify: (id: string) => void;
}

const ApplicationCard: React.FC<ApplicationCardProps> = ({
  application,
  userRole,
  onStatusChange,
  onFileUpload,
  onVerify,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "approved":
        return "bg-green-100 text-green-800 border-green-200";
      case "rejected":
        return "bg-red-100 text-red-800 border-red-200";
      case "verified":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === "application/pdf") {
      onFileUpload(application.id, file);
    }
  };

  // Company can take actions when status is pending
  const canShowCompanyActions =
    userRole === "company" && application.status === "pending";

  // Company can upload proof document after approving (but before candidate verifies)
  const canShowFileUpload =
    userRole === "company" &&
    application.status === "approved" &&
    !application.companyAction?.proofDocument;

  // Candidate can verify when there's a proof document and status is approved
  const canShowVerification =
    userRole === "candidate" &&
    application.status === "approved" &&
    application.companyAction?.proofDocument;
  // &&
  // !application.candidateVerified;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all duration-300 hover:border-gray-300">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-semibold text-gray-900 mb-1">
            {application.job.title}
          </h3>
          <p className="text-gray-600 font-medium">
            {application.company?.companyName || "-"}
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(
            application.status
          )}`}
        >
          {application.status.charAt(0).toUpperCase() +
            application.status.slice(1)}
        </span>
      </div>

      <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
        <div className="flex items-center gap-1">
          <MapPin className="w-4 h-4" />
          <span>{application.job.location || "-"}</span>
        </div>
        <div className="flex items-center gap-1">
          <Calendar className="w-4 h-4" />
          <span>
            Applied {new Date(application.appliedAt).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Show applicant info for both roles but with different labels */}
      <div className="mb-4">
        <p className="text-sm text-gray-600">
          <span className="font-medium">
            {userRole === "candidate" ? "Candidate" : "Applicant"}:
          </span>{" "}
          {application?.candidate.name || "-"}
        </p>
        <p className="text-sm text-gray-600">
          <span className="font-medium">Email:</span>{" "}
          {application.candidate.candidateId || "-"}
        </p>
      </div>

      {/* Company Actions - Only show when status is pending */}
      {canShowCompanyActions && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-3">
            Review Application:
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => onStatusChange(application.id, "approved")}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200 text-sm font-medium"
            >
              <Check className="w-4 h-4" />
              Approve
            </button>
            <button
              onClick={() => onStatusChange(application.id, "rejected")}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200 text-sm font-medium"
            >
              <X className="w-4 h-4" />
              Reject
            </button>
          </div>
        </div>
      )}

      {/* File Upload for Company - Show after approval */}
      {canShowFileUpload && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Upload Proof Document (PDF):
          </p>
          <label className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 cursor-pointer text-sm font-medium">
            <Upload className="w-4 h-4" />
            Upload PDF
            <input
              type="file"
              accept="application/pdf"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      )}

      {/* Show uploaded document */}
      {application.companyAction?.proofDocument && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 text-sm">
            <FileText className="w-4 h-4 text-gray-600" />
            <span className="font-medium text-gray-700">
              {application.companyAction.proofDocument.name}
            </span>
            <button className="ml-auto flex items-center gap-1 text-blue-600 hover:text-blue-700 transition-colors">
              <Eye className="w-4 h-4" />
              View
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Uploaded{" "}
            {new Date(
              application.companyAction.proofDocument.uploadDate
            ).toLocaleDateString()}
          </p>
        </div>
      )}

      {/* Candidate Verification - Show when approved with proof document */}
      {canShowVerification && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-gray-700 mb-3">
            <span className="font-medium">Next Step:</span> The company has
            approved your application and uploaded proof. Please verify the
            document to confirm your final status.
          </p>
          <button
            onClick={() => onVerify(application.id)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium"
          >
            <Check className="w-4 h-4" />
            Verify & Confirm Status
          </button>
        </div>
      )}

      {/* Status Messages for Different Scenarios */}
      {application.status === "approved" &&
        userRole === "company" &&
        !application.companyAction?.proofDocument && (
          <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
            <p className="text-sm text-green-800">
              <span className="font-medium">Action Required:</span> Please
              upload the proof document to complete the approval process.
            </p>
          </div>
        )}

      {application.status === "approved" &&
        userRole === "candidate" &&
        !application.companyAction?.proofDocument && (
          <div className="mb-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <p className="text-sm text-yellow-800">
              <span className="font-medium">Waiting:</span> Company is preparing
              the proof document.
            </p>
          </div>
        )}

      {application.status === "verified" && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-800">
            <span className="font-medium">Complete:</span> Application has been
            verified and finalized.
          </p>
        </div>
      )}

      {application.status === "rejected" && (
        <div className="mb-4 p-3 bg-red-50 rounded-lg border border-red-200">
          <p className="text-sm text-red-800">
            <span className="font-medium">Rejected:</span> This application was
            not approved.
          </p>
        </div>
      )}

      {/* Status History */}
      {(application.companyAction || application.candidateVerified) && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Status Timeline
          </h4>
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-gray-600">
              <span>Application submitted</span>
              <span>
                {new Date(application.appliedAt).toLocaleDateString()}
              </span>
            </div>
            {application.companyAction && (
              <div className="flex justify-between text-xs text-gray-600">
                <span>
                  Company {application.companyAction.status} application
                </span>
                <span>
                  {new Date(
                    application.companyAction.actionDate
                  ).toLocaleDateString()}
                </span>
              </div>
            )}
            {application.companyAction?.proofDocument && (
              <div className="flex justify-between text-xs text-gray-600">
                <span>Proof document uploaded</span>
                <span>
                  {new Date(
                    application.companyAction.proofDocument.uploadDate
                  ).toLocaleDateString()}
                </span>
              </div>
            )}
            {application.candidateVerified && application.verificationDate && (
              <div className="flex justify-between text-xs text-gray-600">
                <span>Verified by candidate</span>
                <span>
                  {new Date(application.verificationDate).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicationCard;
