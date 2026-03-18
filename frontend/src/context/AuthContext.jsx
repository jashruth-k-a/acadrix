import { createContext, useContext, useState, useEffect } from "react";
import { getMe } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("acadrix_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("acadrix_token");
    if (token) {
      getMe()
        .then((res) => {
          setUser(res.data);
          localStorage.setItem("acadrix_user", JSON.stringify(res.data));
        })
        .catch(() => logout())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  /**
   * loginUser(token, userData)  — used by Register
   * loginUser(responseData)     — used by Login (res.data has access_token + user)
   */
  const loginUser = (tokenOrData, userData) => {
    let token, userObj;

    if (typeof tokenOrData === "string") {
      // Called as loginUser(token, user)
      token = tokenOrData;
      userObj = userData;
    } else {
      // Called as loginUser(res.data) where res.data = { access_token, user }
      token = tokenOrData.access_token;
      userObj = tokenOrData.user;
    }

    localStorage.setItem("acadrix_token", token);
    localStorage.setItem("acadrix_user", JSON.stringify(userObj));
    setUser(userObj);
  };

  const logout = () => {
    localStorage.removeItem("acadrix_token");
    localStorage.removeItem("acadrix_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, loginUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
