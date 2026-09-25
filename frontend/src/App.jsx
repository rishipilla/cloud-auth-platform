import { useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8011";

function App() {
  const [mode, setMode] = useState("login");

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleChange = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setMessage("");
    setError("");

    const endpoint =
      mode === "login"
        ? `${API_URL}/login`
        : `${API_URL}/register`;

    const body =
      mode === "login"
        ? {
            email: form.email,
            password: form.password,
          }
        : {
            name: form.name,
            email: form.email,
            password: form.password,
          };

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Authentication failed"
        );
      }

      if (mode === "login") {
        localStorage.setItem(
          "access_token",
          data.access_token
        );

        localStorage.setItem(
          "refresh_token",
          data.refresh_token
        );

        localStorage.setItem(
          "user",
          JSON.stringify(data.user)
        );

        setMessage(
          `Welcome back, ${data.user.name}!`
        );
      } else {
        setMessage(
          "Registration successful. You can now log in."
        );

        setMode("login");

        setForm({
          name: "",
          email: form.email,
          password: "",
        });
      }
    } catch (error) {
      setError(error.message);
    }
  };

  return (
    <div className="app">
      <div className="auth-card">

        <div className="brand">
          <h1>Cloud Auth</h1>
          <p>
            Secure Authentication & Authorization Platform
          </p>
        </div>

        <div className="tabs">
          <button
            className={mode === "login" ? "active" : ""}
            onClick={() => {
              setMode("login");
              setError("");
              setMessage("");
            }}
          >
            Login
          </button>

          <button
            className={mode === "register" ? "active" : ""}
            onClick={() => {
              setMode("register");
              setError("");
              setMessage("");
            }}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit}>

          {mode === "register" && (
            <div className="field">
              <label>Name</label>

              <input
                type="text"
                name="name"
                placeholder="Enter your name"
                value={form.name}
                onChange={handleChange}
                required
              />
            </div>
          )}

          <div className="field">
            <label>Email</label>

            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              value={form.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="field">
            <label>Password</label>

            <input
              type="password"
              name="password"
              placeholder="Enter your password"
              value={form.password}
              onChange={handleChange}
              required
            />
          </div>

          <button
            type="submit"
            className="submit-button"
          >
            {mode === "login"
              ? "Login"
              : "Create Account"}
          </button>

        </form>

        {message && (
          <div className="success">
            {message}
          </div>
        )}

        {error && (
          <div className="error">
            {error}
          </div>
        )}

      </div>
    </div>
  );
}

export default App;