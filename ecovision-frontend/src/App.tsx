import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/layout/Navbar";
import { AuthProvider } from "./context/AuthContext";
import RequireAuth from "./components/RequireAuth";
import RequireRole from "./components/RequireRole";
import RequireNonAdmin from "./components/RequireNonAdmin";
import Profile from "./pages/Profile";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import ProjectView from "./pages/ProjectView";
import MyProjects from "./pages/MyProjects";
import CreateProject from "./pages/CreateProject";
import DesignWorkspace from "./pages/DesignWorkspace";
import ProjectsList from "./pages/ProjectsList";
import AdminDashboard from "./pages/AdminBoard";
import Logs from "./pages/logs";
import AIModels from "./pages/models";
import Projects from "./pages/projAdmin";
import Analysis from "./pages/Analysis";
import Materials from "./pages/materials";
import AdminUsers from "./pages/AdminUsers";


function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />

        <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/" element={<RequireNonAdmin><Dashboard /></RequireNonAdmin>} />
        <Route path="/project/:id" element={<RequireNonAdmin><ProjectView /></RequireNonAdmin>} />
        <Route path="/createproject" element={<RequireNonAdmin><CreateProject /></RequireNonAdmin>} />
        <Route path="/designworkspace/:id" element={<RequireNonAdmin><DesignWorkspace /></RequireNonAdmin>} /> 
        <Route path="/myprojects" element={<RequireNonAdmin><MyProjects /></RequireNonAdmin>} />
        <Route path="/projects" element={<RequireNonAdmin><ProjectsList /></RequireNonAdmin>} />
        <Route path="/admin" element={<RequireRole roles={["admin"]}><AdminDashboard /></RequireRole>} />
        <Route path="/profile" element={<RequireAuth><Profile/></RequireAuth>} />
        <Route path="/materials" element={<RequireRole roles={["admin"]}><Materials /></RequireRole>} />
        <Route path="/admin/projects" element={<RequireRole roles={["admin"]}><Projects /></RequireRole>} />
        <Route path="/ai-models" element={<RequireRole roles={["admin"]}><AIModels /></RequireRole>} />
        <Route path="/logs" element={<RequireRole roles={["admin"]}><Logs /></RequireRole>} />
        <Route path="/analysis/:id" element={<Analysis />} />
        <Route path="/users" element={<RequireRole roles={["admin"]}><AdminUsers /></RequireRole>} />
      </Routes>
   
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

