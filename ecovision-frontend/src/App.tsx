import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/layout/Navbar";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import ProjectView from "./pages/ProjectView";
import MyProjects from "./pages/MyProjects";
import NotFound from "./pages/NotFound";

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
        <Route path="/myprojects" element={<MyProjects />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
