export default function AuthLoading() {
    return (<main className="flex min-h-[100dvh] items-center justify-center bg-canvas px-4">
      <div className="w-full max-w-[420px] rounded-workspace border border-border bg-surface p-8">
        <div className="skeleton h-8 w-48"/>
        <div className="skeleton mt-3 h-4 w-72 max-w-full"/>
        <div className="skeleton mt-8 h-11 w-full"/>
        <div className="skeleton mt-5 h-11 w-full"/>
      </div>
    </main>);
}
