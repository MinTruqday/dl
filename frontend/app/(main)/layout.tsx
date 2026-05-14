import Workspace from "@/components/Workspace";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Workspace requireAuth={true}>{children}</Workspace>;
}
