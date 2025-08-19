// ABOUTME: Simple layout for study initialization without dynamic sidebar
// ABOUTME: Provides clean interface during initialization process

// This layout intentionally overrides the parent study layout to avoid showing
// the sidebar during initialization since the study menu might not be ready yet
export default function InitializationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Return a complete layout to prevent parent layout from wrapping
  return children;
}