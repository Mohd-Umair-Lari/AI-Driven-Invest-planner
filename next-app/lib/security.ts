import bcrypt from "bcryptjs";

export function passwordIssues(password: string): string[] {
  const issues: string[] = [];
  if (password.length < 8) issues.push("Password must be at least 8 characters");
  if (!/[A-Z]/.test(password)) issues.push("Must contain uppercase letter");
  if (!/[a-z]/.test(password)) issues.push("Must contain lowercase letter");
  if (!/[0-9]/.test(password)) issues.push("Must contain number");
  if (!/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) issues.push("Must contain special character");
  return issues;
}

export async function hashPassword(password: string) { return bcrypt.hash(password, 12); }
export async function verifyPassword(password: string, stored: string) {
  if (!stored) return false;
  if (/^\$2[aby]\$/.test(stored)) return bcrypt.compare(password, stored);
  return password === stored;
}
