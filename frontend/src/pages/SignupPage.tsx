import { Link } from "react-router-dom";
import { SignupForm } from "../features/account/SignupForm";

export function SignupPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-900 px-4">
      <div className="w-full max-w-[360px] rounded-lg border border-gray-700 bg-gray-800 p-6">
        <h1 className="text-2xl font-semibold text-gray-100 mb-1">Create your account</h1>
        <p className="text-sm text-gray-400 mb-6">Tech Market Intelligence Platform</p>
        <SignupForm />
        <p className="mt-4 text-xs text-gray-500">
          Already have an account?{" "}
          <Link to="/login" className="text-gray-300 hover:text-gray-100">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
