// ABOUTME: Data management overview page
// ABOUTME: Redirects to data sources as the default data management view

import { redirect } from 'next/navigation';

export default function DataPage() {
  redirect('/data/sources');
}