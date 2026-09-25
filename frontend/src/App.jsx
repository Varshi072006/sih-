import { Navigate, Route, Routes } from "react-router-dom";
import PublicLayout from "./layouts/PublicLayout";
import Protected from "./components/Protected";
import HomePage from "./pages/public/HomePage";
import ProblemsPage from "./pages/public/ProblemsPage";
import ProblemDetailPage from "./pages/public/ProblemDetailPage";
import UniversitiesPublicPage from "./pages/public/UniversitiesPublicPage";
import IndustryPublicPage from "./pages/public/IndustryPublicPage";
import ProjectsPage from "./pages/public/ProjectsPage";
import ProjectDetailPage from "./pages/public/ProjectDetailPage";
import ImpactPage from "./pages/public/ImpactPage";
import HowItWorksPage from "./pages/public/HowItWorksPage";
import LoginPage from "./pages/auth/LoginPage";
import RegisterIndexPage from "./pages/auth/RegisterIndexPage";
import CitizenRegisterPage from "./pages/auth/CitizenRegisterPage";
import UniversityRegisterPage from "./pages/auth/UniversityRegisterPage";
import IndustryRegisterPage from "./pages/auth/IndustryRegisterPage";
import GovernmentRegisterPage from "./pages/auth/GovernmentRegisterPage";
import CitizenDashboard from "./pages/citizen/CitizenDashboard";
import SubmitProblemPage from "./pages/citizen/SubmitProblemPage";
import { GovernmentDashboard, GovernmentDepartments, GovernmentOpinions, GovernmentProblemDetail, GovernmentProblems, GovernmentSolutions, GovernmentTracking } from "./pages/government/GovernmentPortal";
import { UniversityDashboard, UniversityProblemReview, UniversityProblems } from "./pages/university/UniversityPortal";
import { IndustryDashboard, IndustryProblemPage, IndustryProblems } from "./pages/industry/IndustryPortal";
import { AdminAI, AdminAnalytics, AdminAudit, AdminDashboard, AdminIndustries, AdminProblems, AdminProjects, AdminUniversities, AdminUsers } from "./pages/admin/AdminPortal";
import { useAuth } from "./context/AuthContext";

function Public({ children }) {
  return <PublicLayout>{children}</PublicLayout>;
}

function DashRedirect() {
  const { dashboardPath, user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" />;
  return <Navigate to={dashboardPath()} />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Public><HomePage /></Public>} />
      <Route path="/problems" element={<Public><ProblemsPage /></Public>} />
      <Route path="/problem/:id" element={<Public><ProblemDetailPage /></Public>} />
      <Route path="/universities" element={<Public><UniversitiesPublicPage /></Public>} />
      <Route path="/industry" element={<Public><IndustryPublicPage /></Public>} />
      <Route path="/projects" element={<Public><ProjectsPage /></Public>} />
      <Route path="/project/:id" element={<Public><ProjectDetailPage /></Public>} />
      <Route path="/impact" element={<Public><ImpactPage /></Public>} />
      <Route path="/how-it-works" element={<Public><HowItWorksPage /></Public>} />
      <Route path="/login" element={<Public><LoginPage /></Public>} />
      <Route path="/login/citizen" element={<Public><LoginPage title="Citizen Login" expected="citizen" /></Public>} />
      <Route path="/university/login" element={<Public><LoginPage title="University Login" expected="university" /></Public>} />
      <Route path="/industry/login" element={<Public><LoginPage title="Industry Login" expected="industry" /></Public>} />
      <Route path="/government/login" element={<Public><LoginPage title="Government Login" expected="government" /></Public>} />
      <Route path="/admin/login" element={<Public><LoginPage title="Admin Login" expected="admin" /></Public>} />
      <Route path="/register" element={<Public><RegisterIndexPage /></Public>} />
      <Route path="/register/citizen" element={<Public><CitizenRegisterPage /></Public>} />
      <Route path="/register/university" element={<Public><UniversityRegisterPage /></Public>} />
      <Route path="/university/register" element={<Public><UniversityRegisterPage /></Public>} />
      <Route path="/register/industry" element={<Public><IndustryRegisterPage /></Public>} />
      <Route path="/industry/register" element={<Public><IndustryRegisterPage /></Public>} />
      <Route path="/register/government" element={<Public><GovernmentRegisterPage /></Public>} />
      <Route path="/dashboard" element={<DashRedirect />} />

      <Route path="/citizen/dashboard" element={<Protected roles={["citizen"]}><CitizenDashboard /></Protected>} />
      <Route path="/citizen/problems/new" element={<Protected roles={["citizen"]}><SubmitProblemPage /></Protected>} />

      <Route path="/government/dashboard" element={<Protected roles={["government_officer","government_department"]}><GovernmentDashboard /></Protected>} />
      <Route path="/government/problems" element={<Protected roles={["government_officer","government_department"]}><GovernmentProblems /></Protected>} />
      <Route path="/government/tracking" element={<Protected roles={["government_officer","government_department"]}><GovernmentTracking /></Protected>} />
      <Route path="/government/problem/:id" element={<Protected roles={["government_officer","government_department"]}><GovernmentProblemDetail /></Protected>} />
      <Route path="/government/departments" element={<Protected roles={["government_officer","government_department"]}><GovernmentDepartments /></Protected>} />
      <Route path="/government/opinions" element={<Protected roles={["government_officer","government_department"]}><GovernmentOpinions /></Protected>} />
      <Route path="/government/solutions" element={<Protected roles={["government_officer","government_department"]}><GovernmentSolutions /></Protected>} />

      <Route path="/university/dashboard" element={<Protected roles={["university","faculty","student"]}><UniversityDashboard /></Protected>} />
      <Route path="/university/problems" element={<Protected roles={["university","faculty","student"]}><UniversityProblems /></Protected>} />
      <Route path="/university/problem/:id" element={<Protected roles={["university","faculty","student"]}><UniversityProblemReview /></Protected>} />
      <Route path="/university/opinion/:id" element={<Protected roles={["university","faculty","student"]}><UniversityProblemReview /></Protected>} />

      <Route path="/industry/dashboard" element={<Protected roles={["industry","startup","msme","csr"]}><IndustryDashboard /></Protected>} />
      <Route path="/industry/problems" element={<Protected roles={["industry","startup","msme","csr"]}><IndustryProblems /></Protected>} />
      <Route path="/industry/problem/:id" element={<Protected roles={["industry","startup","msme","csr"]}><IndustryProblemPage /></Protected>} />

      <Route path="/admin/dashboard" element={<Protected roles={["admin","super_admin"]}><AdminDashboard /></Protected>} />
      <Route path="/admin/users" element={<Protected roles={["admin","super_admin"]}><AdminUsers /></Protected>} />
      <Route path="/admin/problems" element={<Protected roles={["admin","super_admin"]}><AdminProblems /></Protected>} />
      <Route path="/admin/universities" element={<Protected roles={["admin","super_admin"]}><AdminUniversities /></Protected>} />
      <Route path="/admin/industries" element={<Protected roles={["admin","super_admin"]}><AdminIndustries /></Protected>} />
      <Route path="/admin/projects" element={<Protected roles={["admin","super_admin"]}><AdminProjects /></Protected>} />
      <Route path="/admin/ai" element={<Protected roles={["admin","super_admin"]}><AdminAI /></Protected>} />
      <Route path="/admin/analytics" element={<Protected roles={["admin","super_admin"]}><AdminAnalytics /></Protected>} />
      <Route path="/admin/audit-logs" element={<Protected roles={["admin","super_admin"]}><AdminAudit /></Protected>} />
    </Routes>
  );
}
