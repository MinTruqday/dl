import { Suspense } from "react";
import AuthLoading from "@/features/authentication/components/AuthLoading";
export default function AuthLayout({ children, }) {
    return <Suspense fallback={<AuthLoading />}>{children}</Suspense>;
}
