import ProjectWorkspacePage from "@/features/testing/pages/ProjectWorkspacePage";

export default async function Page({ params, searchParams }) {
  const values = await params;
  const query = await searchParams;
  return (
    <ProjectWorkspacePage
      projectId={values.projectId}
      section={values.section || []}
      initialQuery={query?.q || ""}
    />
  );
}
