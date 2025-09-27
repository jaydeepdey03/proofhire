import React, { useState } from "react";
import {
  Bot,
  Settings,
  Play,
  Pause,
  Star,
  Target,
  Zap,
  TrendingUp,
  CheckCircle,
  AlertTriangle,
  Clock,
} from "lucide-react";

export const AIAgent: React.FC = () => {
  const [agentActive, setAgentActive] = useState(true);
  const [minCompatibilityScore, setMinCompatibilityScore] = useState(75);
  const [maxApplicationsPerDay, setMaxApplicationsPerDay] = useState(5);
  const [preferredLocations, setPreferredLocations] = useState([
    "San Francisco",
    "Remote",
  ]);

  // const candidate = user as Candidate;
  // const aiApplications = applications.filter(
  //   (app) => app.candidateId === candidate.id && app.aiApplied
  // );

  // const todayApplications = aiApplications.filter((app) => {
  //   const today = new Date();
  //   const appDate = new Date(app.appliedAt);
  //   return appDate.toDateString() === today.toDateString();
  // });

  // const potentialJobs = jobs.filter((job) => {
  //   const compatibility = getCompatibilityScore(job, candidate);
  //   const alreadyApplied = applications.some(
  //     (app) => app.jobId === job.id && app.candidateId === candidate.id
  //   );
  //   const locationMatch = preferredLocations.some((loc) =>
  //     job.location.toLowerCase().includes(loc.toLowerCase())
  //   );
  //   const notExcluded = !excludedCompanies.includes(job.company.companyName);

  //   return (
  //     compatibility >= minCompatibilityScore &&
  //     !alreadyApplied &&
  //     locationMatch &&
  //     notExcluded
  //   );
  // });

  const stats = [
    {
      label: "Auto Applications",
      value: 12,
      icon: Bot,
      color: "bg-purple-500",
      change: "+12 this week",
    },
    {
      label: "Today's Applications",
      value: 3,
      icon: Clock,
      color: "bg-blue-500",
      change: "2 remaining",
    },
    {
      label: "Success Rate",
      value: "68%",
      icon: TrendingUp,
      color: "bg-green-500",
      change: "+5% vs manual",
    },
    {
      label: "Potential Matches",
      value: 15,
      icon: Target,
      color: "bg-orange-500",
      change: "Available now",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Job Agent</h1>
          <p className="text-gray-600 mt-1">
            Let AI automatically apply to relevant jobs based on your
            preferences
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              agentActive
                ? "bg-green-100 text-green-800"
                : "bg-gray-100 text-gray-800"
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full mr-2 ${
                agentActive ? "bg-green-500 animate-pulse" : "bg-gray-400"
              }`}
            ></div>
            {agentActive ? "Active" : "Paused"}
          </span>
          <button
            onClick={() => setAgentActive(!agentActive)}
            className={`px-4 py-2 rounded-lg font-semibold transition-colors flex items-center space-x-2 ${
              agentActive
                ? "bg-red-600 hover:bg-red-700 text-white"
                : "bg-green-600 hover:bg-green-700 text-white"
            }`}
          >
            {agentActive ? (
              <>
                <Pause className="w-4 h-4" />
                <span>Pause Agent</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Start Agent</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="bg-white p-6 rounded-xl shadow-sm border border-gray-100"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">
                    {stat.label}
                  </p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">
                    {stat.value}
                  </p>
                </div>
                <div
                  className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}
                >
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
              <div className="mt-4">
                <span className="text-sm text-gray-600">{stat.change}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Agent Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center space-x-3 mb-4">
            <Settings className="w-6 h-6 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              Agent Settings
            </h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Compatibility Score
              </label>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="50"
                  max="95"
                  value={minCompatibilityScore}
                  onChange={(e) =>
                    setMinCompatibilityScore(parseInt(e.target.value))
                  }
                  className="flex-1"
                />
                <span className="text-sm font-medium text-gray-900 w-12">
                  {minCompatibilityScore}%
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Only apply to jobs with compatibility score above this threshold
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Applications Per Day
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={maxApplicationsPerDay}
                onChange={(e) =>
                  setMaxApplicationsPerDay(parseInt(e.target.value) || 1)
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                Limit daily applications to maintain quality over quantity
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preferred Locations
              </label>
              <div className="space-y-2">
                {preferredLocations.map((location, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => {
                        const newLocations = [...preferredLocations];
                        newLocations[index] = e.target.value;
                        setPreferredLocations(newLocations);
                      }}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      onClick={() => {
                        setPreferredLocations(
                          preferredLocations.filter((_, i) => i !== index)
                        );
                      }}
                      className="text-red-600 hover:text-red-700"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  onClick={() =>
                    setPreferredLocations([...preferredLocations, ""])
                  }
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  + Add Location
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center space-x-3 mb-4">
            <Zap className="w-6 h-6 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">AI Insights</h3>
          </div>

          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-start space-x-3">
                <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-blue-900">
                    Optimization Tip
                  </h4>
                  <p className="text-sm text-blue-800 mt-1">
                    Your current settings will match {"potentialJobs.length"}{" "}
                    jobs. Consider lowering the compatibility threshold to{" "}
                    {minCompatibilityScore - 10}% to increase opportunities by
                    40%.
                  </p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-start space-x-3">
                <TrendingUp className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-green-900">
                    Performance Update
                  </h4>
                  <p className="text-sm text-green-800 mt-1">
                    AI applications have a 68% higher response rate compared to
                    manual applications. Your personalized approach is working
                    well!
                  </p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-yellow-900">
                    Market Alert
                  </h4>
                  <p className="text-sm text-yellow-800 mt-1">
                    There's been a 25% increase in React developer positions
                    this week. Consider increasing your daily application limit
                    temporarily.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-xl border border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Ready to Apply
            </h3>
            <p className="text-gray-600">
              15 high-quality matches found based on your preferences. AI can
              apply to 2 more jobs today.
            </p>
          </div>
          <div className="flex space-x-3">
            {/* <button
              onClick={handleAutoApply}
              disabled={
                !agentActive ||
                todayApplications.length >= maxApplicationsPerDay
              }
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            >
              Apply Now (
              {Math.min(
                potentialJobs.length,
                maxApplicationsPerDay - todayApplications.length
              )}
              )
            </button> */}
            <button className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
              Review Matches
            </button>
          </div>
        </div>
      </div>

      {/* Recent AI Applications */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Recent AI Applications
        </h3>

        {[].length === 0 ? (
          <div className="text-center py-8">
            <Bot className="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500">No AI applications yet</p>
            <p className="text-sm text-gray-400">
              Activate your AI agent to start auto-applying
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5, 6].slice(0, 5).map((application) => (
              <div
                key={application}
                className="flex items-center justify-between p-3 bg-purple-50 rounded-lg border border-purple-200"
              >
                <div className="flex items-center space-x-3">
                  <Bot className="w-5 h-5 text-purple-600" />
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {"application.job.title"}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {"application.job.company.companyName"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1">
                    <Star className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm font-medium">
                      {"application.compatibilityScore"}%
                    </span>
                  </div>
                  {/* <span
                    className={`px-2 py-1 text-xs font-medium rounded-full ${
                      application.status === "pending"
                        ? "bg-yellow-100 text-yellow-800"
                        : application.status === "application_accepted"
                        ? "bg-blue-100 text-blue-800"
                        : "bg-green-100 text-green-800"
                    }`}
                  >
                    {application.status.replace("_", " ")}
                  </span> */}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};