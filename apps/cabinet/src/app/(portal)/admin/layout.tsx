import Link from "next/link";
import { notFound } from "next/navigation";
import { requireSession } from "@/lib/session";

// UI gate only: the BL re-checks the admin role on every /v1/admin/* call (ADR-0019).
export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const session = await requireSession("/app/admin");
  if (!session.roles.includes("admin")) notFound();
  return (
    <>
      <nav className="mb-8 flex flex-wrap gap-2 text-sm">
        {[
          ["/admin", "Сводка"],
          ["/admin/users", "Пользователи"],
          ["/admin/runs", "Запуски"],
          ["/admin/agents", "Агенты и квота"],
        ].map(([href, label]) => (
          <Link key={href} href={href} className="btn btn-ghost">
            {label}
          </Link>
        ))}
      </nav>
      {children}
    </>
  );
}
