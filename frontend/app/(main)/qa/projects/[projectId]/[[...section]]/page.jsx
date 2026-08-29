import ProjectWorkspacePage from "@/features/testing/pages/ProjectWorkspacePage";

export default async function Page({ params }) {
  const values = await params;
  return <ProjectWorkspacePage projectId={values.projectId} section={values.section || []} />;
}
