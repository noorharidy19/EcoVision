import React, { useEffect, useState } from "react";
import "../styles/Adminuser.css";

type User = {
  id: number;
  email: string;
  full_name: string;
  phone_number: string;
  role: string;
};

const AdminUsers: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
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

  const filteredUsers = users.filter((user) => {
  const search = searchTerm.toLowerCase();

  return (
    user.full_name.toLowerCase().includes(search) ||
    user.phone_number.toString().includes(search)
  );
});


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

  const handleDelete = async (id: number) => {
    await fetch(`http://127.0.0.1:8000/admin/users/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    fetchUsers();
  };

  const handleEdit = (user: User) => {
    setEditingUserId(user.id);
    setEditedUser({ ...user });
  };

  const handleSave = async () => {
    if (!editedUser) return;

    await fetch(`http://127.0.0.1:8000/admin/users/${editedUser.id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        email: editedUser.email,
        full_name: editedUser.full_name,
        phone_number: editedUser.phone_number,
        role: editedUser.role,
        password: null,
      }),
    });

    setEditingUserId(null);
    setEditedUser(null);
    fetchUsers();
  };

  return (
    <div className="admin-page">
      <h1 className="admin-title">All Users (Admin View)</h1>
        <div className="search-container">
  <input
    type="text"
    placeholder="Search by Name or Phone number..."
    value={searchTerm}
    onChange={(e) => setSearchTerm(e.target.value)}
    className="search-input"
  />
</div>
       
      {/* ADD USER CARD */}
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

      {/* USERS CARDS */}
      <div className="admin-cards">
        {filteredUsers.map((user) => (
          <div className="admin-card" key={user.id}>
            {editingUserId === user.id ? (
              <>
                <input
                  value={editedUser?.full_name || ""}
                  onChange={(e) =>
                    setEditedUser({ ...editedUser!, full_name: e.target.value })
                  }
                />
                <input
                  value={editedUser?.email || ""}
                  onChange={(e) =>
                    setEditedUser({ ...editedUser!, email: e.target.value })
                  }
                />
                <input
                  value={editedUser?.phone_number || ""}
                  onChange={(e) =>
                    setEditedUser({ ...editedUser!, phone_number: e.target.value })
                  }
                />
                <select
                  value={editedUser?.role || ""}
                  onChange={(e) =>
                    setEditedUser({ ...editedUser!, role: e.target.value })
                  }
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>

                <div className="card-actions">
                  <button onClick={handleSave}>Save</button>
                  <button className="danger" onClick={() => setEditingUserId(null)}>
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <>
                <h3>{user.full_name}</h3>
                <p><strong>Email:</strong> {user.email}</p>
                <p><strong>Phone:</strong> {user.phone_number}</p>
                <p><strong>Role:</strong> {user.role}</p>

                <div className="card-actions">
                  <button onClick={() => handleEdit(user)}>Edit</button>
                  <button className="danger" onClick={() => handleDelete(user.id)}>
                    Delete
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AdminUsers;
