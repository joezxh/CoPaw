import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button, Form, Input } from "antd";
import { useAppMessage } from "../../hooks/useAppMessage";
import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { authApi } from "../../api/modules/auth";
import { enterpriseAuthApi } from "../../api/modules/enterprise-auth";
import { setAuthToken, setAuthDisabled } from "../../api/config";
import { useTheme } from "../../contexts/ThemeContext";

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isDark } = useTheme();
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [hasUsers, setHasUsers] = useState(true);
  const [isEnterprise, setIsEnterprise] = useState(false);
  const { message } = useAppMessage();
  const hasCheckedAuth = useRef(false);

  useEffect(() => {
    // Prevent duplicate execution (useRef persists across re-renders but not remounts)
    if (hasCheckedAuth.current) {
      return;
    }
    hasCheckedAuth.current = true;
    
    // Try to detect auth mode by checking /api/auth/status
    authApi
      .getStatus()
      .then((res) => {
        if (!res.enabled) {
          // Auth disabled - set global flag and navigate to chat
          setAuthDisabled(true);
          navigate("/chat", { replace: true });
          return;
        }
        
        // Auth is enabled
        setAuthDisabled(false);
        setIsEnterprise(res.is_enterprise || false);
        
        // Auth is enabled, check if there are users
        setHasUsers(res.has_users);
        if (!res.has_users) {
          setIsRegister(true);
        }
      })
      .catch(() => {
        // If /api/auth/status fails, default to showing login form
        setHasUsers(true);
        setIsRegister(false);
      });
  }, [navigate]);

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const raw = searchParams.get("redirect") || "/chat";
      const redirect =
        raw.startsWith("/") && !raw.startsWith("//") ? raw : "/chat";

      if (isRegister) {
        if (isEnterprise) {
          await enterpriseAuthApi.register({
            username: values.username,
            password: values.password,
          });
          message.success(t("login.registerSuccess"));
          // After registration, auto-login
          const loginRes = await enterpriseAuthApi.login({
            username: values.username,
            password: values.password,
          });
          setAuthToken(loginRes.access_token);
          navigate(redirect, { replace: true });
        } else {
          const res = await authApi.register(values.username, values.password);
          if (res.token) {
            setAuthToken(res.token);
            message.success(t("login.registerSuccess"));
            navigate(redirect, { replace: true });
          }
        }
      } else {
        if (isEnterprise) {
          const res = await enterpriseAuthApi.login({
            username: values.username,
            password: values.password,
          });
          setAuthToken(res.access_token);
          navigate(redirect, { replace: true });
        } else {
          const res = await authApi.login(values.username, values.password);
          if (res.token) {
            setAuthToken(res.token);
            navigate(redirect, { replace: true });
          } else {
            message.info(t("login.authNotEnabled"));
            navigate(redirect, { replace: true });
          }
        }
      }
    } catch (err: any) {
      message.error(
        isRegister
          ? err?.message || err?.detail || t("login.registerFailed")
          : err?.message || err?.detail || t("login.failed"),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: isDark
          ? "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)"
          : "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
      }}
    >
      <div
        style={{
          width: 400,
          padding: 32,
          borderRadius: 12,
          background: isDark ? "#1f1f1f" : "#fff",
          boxShadow: isDark
            ? "0 4px 24px rgba(0,0,0,0.4)"
            : "0 4px 24px rgba(0,0,0,0.1)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <img
            src={`${import.meta.env.BASE_URL}${
              isDark ? "dark-logo.png" : "logo.png"
            }`}
            alt="CoPaw"
            style={{ height: 48, marginBottom: 12 }}
          />
          <h2 style={{ margin: 0, fontWeight: 600, fontSize: 20 }}>
            {isRegister ? t("login.registerTitle") : t("login.title")}
          </h2>
          {!hasUsers && (
            <p
              style={{
                margin: "8px 0 0",
                color: isDark ? "rgba(255,255,255,0.45)" : "#666",
                fontSize: 13,
              }}
            >
              {t("login.firstUserHint")}
            </p>
          )}
        </div>

        <Form
          layout="vertical"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
          initialValues={{ username: "admin" }}
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: t("login.usernameRequired") }]}
          >
            <Input
              prefix={
                <UserOutlined
                  style={{
                    color: isDark ? "rgba(255,255,255,0.45)" : undefined,
                  }}
                />
              }
              placeholder={t("login.usernamePlaceholder")}
              autoFocus
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: t("login.passwordRequired") }]}
          >
            <Input.Password
              prefix={
                <LockOutlined
                  style={{
                    color: isDark ? "rgba(255,255,255,0.45)" : undefined,
                  }}
                />
              }
              placeholder={t("login.passwordPlaceholder")}
              autoComplete="new-password"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{ height: 44, borderRadius: 8, fontWeight: 500 }}
            >
              {isRegister ? t("login.register") : t("login.submit")}
            </Button>
          </Form.Item>
          
          {/* Toggle between login and register */}
          <Form.Item style={{ marginBottom: 0, marginTop: 16, textAlign: "center" }}>
            <a
              onClick={() => setIsRegister(!isRegister)}
              style={{ color: "#1677ff", cursor: "pointer" }}
            >
              {isRegister
                ? t("login.alreadyHaveAccount") || "Already have an account? Login"
                : t("login.noAccount") || "No account? Register first"}
            </a>
          </Form.Item>
        </Form>
      </div>
    </div>
  );
}
