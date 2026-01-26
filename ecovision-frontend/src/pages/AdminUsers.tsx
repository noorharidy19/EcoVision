import React, { useEffect, useState } from "react";
import "../styles/Admin.css";

type User = {
  id: number;
  email: string;
  full_name: string;
  phone_number: string;
  role: string;
};

const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editedUser, setEditedUser] = useState<User | null>(null);

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  const token = localStorage.getItem("token");

  const fetchUsers = async () => {
    const res = await fetch("http://127.0.0.1:8000/admin/users", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    setUsers(data);
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Create user
  const handleCreateUser = async () => {
    await fetch("http://127.0.0.1:8000/admin/users", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        email,
        full_name: fullName,
        phone_number: phone,
        password,
        role: "user",
      }),
    });

    setEmail("");
    setFullName("");
    setPhone("");
    setPassword("");
    fetchUsers();
  };

  // Delete user
  const handleDelete = async (id: number) => {
    await fetch(`http://127.0.0.1:8000/admin/users/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    fetchUsers();
  };

  // Start editing
  const handleEdit = (user: User) => {
    setEditingUserId(user.id);
    setEditedUser({ ...user });
  };

  // Save edited user
  const handleSave = async () => {
  if (!editedUser) return;

  const res = await fetch(`http://127.0.0.1:8000/admin/users/${editedUser.id}`, {
    method: "PUT", // if backend uses PATCH, change this to PATCH
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      email: editedUser.email,
      full_name: editedUser.full_name,
      phone_number: editedUser.phone_number,
      role: editedUser.role,
      password: null
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    console.error("Update failed:", err);
    alert("Failed to update user");
    return;
  }

   
  setEditingUserId(null);
  setEditedUser(null);
  fetchUsers();
  console.log("Saving user:", editedUser);

};

  return (
    <div className="admin-page">
      <h2 className="admin-title">Manage Users</h2>

      {/* Add user */}
      <div className="admin-card">
        <h3>Add New User</h3>
        <div className="admin-form">
          <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input placeholder="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <input placeholder="Phone Number" value={phone} onChange={(e) => setPhone(e.target.value)} />
          <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button onClick={handleCreateUser}>Add User</button>
        </div>
      </div>

      {/* Users table */}
      <div className="admin-card">
        <h3>All Users</h3>

        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>Name</th>
              <th>Phone</th>
              <th>Role</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>

                {editingUserId === user.id ? (
                  <>
                    <td>
                      <input
                        value={editedUser?.email || ""}
                        onChange={(e) =>
                          setEditedUser({ ...editedUser!, email: e.target.value })
                        }
                      />
                    </td>

                    <td>
                      <input
                        value={editedUser?.full_name || ""}
                        onChange={(e) =>
                          setEditedUser({ ...editedUser!, full_name: e.target.value })
                        }
                      />
                    </td>

                    <td>
                      <input
                        value={editedUser?.phone_number || ""}
                        onChange={(e) =>
                          setEditedUser({ ...editedUser!, phone_number: e.target.value })
                        }
                      />
                    </td>

                    <td>
                      <select
                        value={editedUser?.role || ""}
                        onChange={(e) =>
                          setEditedUser({ ...editedUser!, role: e.target.value })
                        }
                      >
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>

                    <td>
                      <button onClick={handleSave}>Save</button>
                      <button onClick={() => setEditingUserId(null)}>Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td>{user.email}</td>
                    <td>{user.full_name}</td>
                    <td>{user.phone_number}</td>
                    <td>{user.role}</td>
                    <td>
                      <button onClick={() => handleEdit(user)}>Edit</button>
                      <button onClick={() => handleDelete(user.id)}>Delete</button>
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminUsers;
