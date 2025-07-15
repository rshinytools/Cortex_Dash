// ABOUTME: Simple layout for study initialization without dynamic sidebar
// ABOUTME: Provides clean interface during initialization process

export default function InitializationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      {children}
    </div>
  );
}