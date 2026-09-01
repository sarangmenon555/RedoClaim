"use client";
import { useState, useEffect } from "react";
import { authApi } from "@/lib/api";
import toast from "react-hot-toast";
import {
  User, Phone, Save, Loader2, CheckCircle, Shield,
  LogOut, Lock, Trash2, AlertTriangle, Eye, EyeOff, Languages
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useLanguageStore } from "@/store/language";
import { SUPPORTED_LANGUAGES, isSupportedLanguage } from "@/lib/i18n/languages";

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [email, setEmail] = useState("");

  // Profile form
  const [profile, setProfile] = useState({ full_name: "", phone: "" });
  const { language, setLanguage } = useLanguageStore();
  const [savingLanguage, setSavingLanguage] = useState(false);

  // Password form
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [showPasswords, setShowPasswords] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);

  // Delete account
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    authApi.me().then((r) => {
      setProfile({
        full_name: r.data.full_name || "",
        phone: r.data.phone || "",
      });
      setEmail(r.data.email || "");
      if (isSupportedLanguage(r.data.preferred_language)) {
        setLanguage(r.data.preferred_language);
      }
    }).catch(() => {
      toast.error("Could not load profile");
    }).finally(() => setLoading(false));
  }, []);

  const handleSaveLanguage = async (code: string) => {
    setLanguage(code);
    setSavingLanguage(true);
    try {
      await authApi.updateProfile({ preferred_language: code });
      toast.success("Report language updated");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not save language preference");
    } finally {
      setSavingLanguage(false);
    }
  };

  const handleSaveProfile = async () => {
    if (!profile.full_name.trim()) {
      toast.error("Full name cannot be empty");
      return;
    }
    setSaving(true);
    try {
      await authApi.updateProfile({
        full_name: profile.full_name.trim(),
        phone: profile.phone.trim() || null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
      toast.success("Profile updated — your name will appear in new appeal letters");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Update failed");
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (!passwordForm.current_password) {
      toast.error("Enter your current password");
      return;
    }
    if (passwordForm.new_password.length < 8) {
      toast.error("New password must be at least 8 characters");
      return;
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error("New passwords do not match");
      return;
    }
    setSavingPassword(true);
    try {
      await authApi.changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
      toast.success("Password changed successfully");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Password change failed");
    } finally {
      setSavingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE") {
      toast.error("Type DELETE to confirm");
      return;
    }
    setDeleting(true);
    try {
      await authApi.deleteAccount();
      toast.success("Account deleted");
      router.push("/auth/login");
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Delete failed");
      setDeleting(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/auth/login");
  };

  if (loading) {
    return (
      <div className="max-w-2xl flex items-center justify-center py-24">
        <Loader2 className="animate-spin text-violet-400" size={32} />
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in" style={{ color: "var(--text-primary)" }}>
      <div>
        <h2 className="text-2xl font-bold style-text-primary">Settings</h2>
        <p className="style-text-tertiary text-sm mt-1">
          Manage your profile, password, and account.
        </p>
      </div>

      {/* ── Profile ── */}
      <div className="card p-6 space-y-5">
        <div className="flex items-center gap-2">
          <User size={16} className="text-violet-400" />
          <h3 className="font-semibold style-text-primary">Profile</h3>
        </div>

        <div>
          <label className="label">Email address</label>
          <input className="input opacity-60 cursor-not-allowed" value={email} disabled readOnly />
          <p className="text-xs style-text-tertiary mt-1">Email cannot be changed</p>
        </div>

        <div>
          <label className="label">
            Full name <span className="text-red-500">*</span>
          </label>
          <input
            className="input"
            placeholder="e.g. Rajesh Kumar Menon"
            value={profile.full_name}
            onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
          />
          <p className="text-xs style-text-tertiary mt-1">
            This name appears in all AI-generated appeal letters
          </p>
        </div>

        <div>
          <label className="label flex items-center gap-1.5">
            <Phone size={12} className="style-text-tertiary" />
            Phone number (optional)
          </label>
          <input
            className="input"
            placeholder="e.g. 9447123456"
            value={profile.phone}
            onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
          />
        </div>

        <button onClick={handleSaveProfile} disabled={saving} className="btn-primary">
          {saving ? (
            <><Loader2 size={15} className="animate-spin" /> Saving...</>
          ) : saved ? (
            <><CheckCircle size={15} /> Saved!</>
          ) : (
            <><Save size={15} /> Save changes</>
          )}
        </button>
      </div>

      {/* ── Report Language ── */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <Languages size={16} className="text-violet-400" />
          <h3 className="font-semibold style-text-primary">Report Language</h3>
        </div>
        <p className="text-xs style-text-tertiary -mt-2">
          Choose the language for your audit reports, appeal letters, and guidance.
          Powered by Sarvam AI.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {SUPPORTED_LANGUAGES.map((l) => (
            <button
              key={l.code}
              onClick={() => handleSaveLanguage(l.code)}
              disabled={savingLanguage}
              className="flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-all"
              style={
                l.code === language
                  ? { background: "rgba(139,92,246,0.15)", color: "#C4B5FD", border: "1px solid rgba(139,92,246,0.3)" }
                  : { color: "var(--text-secondary)", border: "1px solid var(--surface-5)" }
              }
            >
              <span>{l.label}</span>
              {l.code === language && <CheckCircle size={14} />}
            </button>
          ))}
        </div>
      </div>

      {/* ── Change Password ── */}
      <div className="card p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lock size={16} className="text-violet-400" />
            <h3 className="font-semibold style-text-primary">Change Password</h3>
          </div>
          <button
            onClick={() => setShowPasswords(!showPasswords)}
            className="text-xs style-text-tertiary flex items-center gap-1 hover:style-text-secondary transition"
          >
            {showPasswords ? <EyeOff size={12} /> : <Eye size={12} />}
            {showPasswords ? "Hide" : "Show"}
          </button>
        </div>

        <div>
          <label className="label">Current password</label>
          <input
            className="input"
            type={showPasswords ? "text" : "password"}
            placeholder="Your current password"
            value={passwordForm.current_password}
            onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
          />
        </div>

        <div>
          <label className="label">New password</label>
          <input
            className="input"
            type={showPasswords ? "text" : "password"}
            placeholder="At least 8 characters"
            value={passwordForm.new_password}
            onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
          />
        </div>

        <div>
          <label className="label">Confirm new password</label>
          <input
            className="input"
            type={showPasswords ? "text" : "password"}
            placeholder="Repeat new password"
            value={passwordForm.confirm_password}
            onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
          />
        </div>

        <button onClick={handleChangePassword} disabled={savingPassword} className="btn-primary">
          {savingPassword
            ? <><Loader2 size={15} className="animate-spin" /> Changing...</>
            : <><Lock size={15} /> Change password</>}
        </button>
      </div>

      {/* ── Account ── */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Shield size={16} className="text-violet-400" />
          <h3 className="font-semibold style-text-primary">Account</h3>
        </div>

        {/* Sign out */}
        <div className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">
          <div>
            <p className="text-sm font-medium style-text-primary">Sign out</p>
            <p className="text-xs style-text-tertiary">Sign out of your RedoClaim account</p>
          </div>
          <button onClick={handleLogout} className="btn-secondary text-sm flex items-center gap-2">
            <LogOut size={14} /> Sign out
          </button>
        </div>

        {/* Delete account */}
        <div className="p-3 border border-red-200 rounded-lg bg-red-50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-red-800">Delete account</p>
              <p className="text-xs text-red-600 mt-0.5">
                Permanently deletes your account, all documents, claims, and appeal letters.
              </p>
            </div>
            <button
              onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
              className="text-xs px-3 py-1.5 rounded-lg border border-red-300 text-red-700 hover:bg-red-100 transition flex items-center gap-1.5 shrink-0 ml-3"
            >
              <Trash2 size={13} /> Delete
            </button>
          </div>

          {showDeleteConfirm && (
            <div className="mt-4 space-y-3 border-t border-red-200 pt-4">
              <div className="flex items-start gap-2">
                <AlertTriangle size={14} className="text-red-600 shrink-0 mt-0.5" />
                <p className="text-xs text-red-800">
                  This action is <strong>permanent and irreversible.</strong> All your
                  documents, claims, and appeal letters will be deleted immediately.
                </p>
              </div>
              <div>
                <label className="text-xs text-red-800 font-medium mb-1 block">
                  Type <strong>DELETE</strong> to confirm
                </label>
                <input
                  className="input border-red-300 text-sm"
                  placeholder="DELETE"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleDeleteAccount}
                  disabled={deleting || deleteConfirmText !== "DELETE"}
                  className="px-4 py-2 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition"
                >
                  {deleting
                    ? <><Loader2 size={13} className="animate-spin" /> Deleting...</>
                    : <><Trash2 size={13} /> Delete my account</>}
                </button>
                <button
                  onClick={() => { setShowDeleteConfirm(false); setDeleteConfirmText(""); }}
                  className="btn-secondary text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="p-3 bg-surface-2 rounded-lg">
          <p className="text-xs style-text-tertiary">
            <strong className="style-text-secondary">Data & Privacy:</strong> Your documents
            and claims are stored securely. RedoClaim does not share your data with insurers
            or third parties.
          </p>
        </div>
      </div>
    </div>
  );
}