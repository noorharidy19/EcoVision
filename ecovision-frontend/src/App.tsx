import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/layout/Navbar";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import ProjectView from "./pages/ProjectView";
import MyProjects from "./pages/MyProjects";
import NotFound from "./pages/NotFound";
import CreateProject from "./pages/CreateProject";
import DesignWorkspace from "./pages/DesignWorkspace";
import ProjectsList from "./pages/ProjectsList";
import AdminDashboard from "./pages/AdminBoard";
import Logs from "./pages/logs";
import AIModels from "./pages/models";
import Projects from "./pages/projAdmin";
import ManageUsers from "./pages/users";
import Materials from "./pages/materials";

function App() {
  return (
    <BrowserRouter>
      <Navbar />  

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/project/:id" element={<ProjectView />} />
        <Route path="*" element={<NotFound />} />
        <Route path="/createproject" element={<CreateProject />} />
        <Route path="/myprojects" element={<MyProjects />} />
        <Route path="/designworkspace" element={<DesignWorkspace />} />
        <Route path="/" element={<ProjectsList />} />
        <Route path="/workspace/:id" element={<DesignWorkspace />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/materials" element={<Materials />} />
        <Route path="/users" element={<ManageUsers />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/ai-models" element={<AIModels />} />
        <Route path="/logs" element={<Logs />} />
      </Routes>
   
    </BrowserRouter>
  );
}

export default App;

