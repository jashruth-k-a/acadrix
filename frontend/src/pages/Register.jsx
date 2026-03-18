import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register } from "../api";          // ✅ was calling undefined `register`
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { loginUser } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await register(form);      // ✅ now correctly imported
      // res.data = { access_token, user }
      loginUser(res.data);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <img
          src="/acadrix-logo.svg"
          className="auth-logo"
          alt="Acadrix"
          onError={(e) => { e.currentTarget.style.display = "none"; }}
        />
        <h2>Create an account</h2>
        <p className="auth-subtitle">Start learning smarter with Acadrix</p>

        <form onSubmit={handleSubmit}>
          {error && <p className="auth-error">{error}</p>}

          <input
            type="text"
            placeholder="Full name"
            value={form.name}
            onChange={handleChange("name")}
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={handleChange("email")}
            required
          />
          <input
            type="password"
            placeholder="Password (min 6 characters)"
            value={form.password}
            onChange={handleChange("password")}
            required
            minLength={6}
          />

          <button type="submit" disabled={loading}>
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{" "}
          <span onClick={() => navigate("/login")}>Sign in</span>
        </p>
      </div>
    </div>
  );
}
