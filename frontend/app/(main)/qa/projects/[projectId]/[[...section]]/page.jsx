import ProjectWorkspacePage from "@/features/qa/pages/ProjectWorkspacePage";

export default async function Page({ params }) {
  const values = await params;
  return <ProjectWorkspacePage projectId={values.projectId} section={values.section || []} />;
}
