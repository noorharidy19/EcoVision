import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/layout/Navbar";
import { AuthProvider } from "./context/AuthContext";
import RequireAuth from "./components/RequireAuth";
import RequireRole from "./components/RequireRole";
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
import ManageUsers from "./pages/users";
import Materials from "./pages/materials";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />

        <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/project/:id" element={<ProjectView />} />
        <Route path="/createproject" element={<CreateProject />} />
        <Route path="/designworkspace" element={<DesignWorkspace />} /> 
        <Route path="/myprojects" element={<MyProjects />} />
        <Route path="/" element={<ProjectsList />} />
        <Route path="/workspace/:id" element={<DesignWorkspace />} />
        <Route path="/admin" element={<RequireRole roles={["admin"]}><AdminDashboard /></RequireRole>} />
        <Route path="/profile" element={<RequireAuth><Profile/></RequireAuth>} />
        <Route path="/materials" element={<RequireRole roles={["admin"]}><Materials /></RequireRole>} />
        <Route path="/users" element={<RequireRole roles={["admin"]}><ManageUsers /></RequireRole>} />
        <Route path="/projects" element={<RequireRole roles={["admin"]}><Projects /></RequireRole>} />
        <Route path="/ai-models" element={<RequireRole roles={["admin"]}><AIModels /></RequireRole>} />
        <Route path="/logs" element={<RequireRole roles={["admin"]}><Logs /></RequireRole>} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
   
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

