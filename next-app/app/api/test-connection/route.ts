import { NextResponse } from "next/server";
import { getDb } from "@/lib/mongo";
export async function GET() {
  try { await getDb().then((db) => db.command({ ping: 1 })); return NextResponse.json({ status: "success", message: "Backend and database connection are working" }); } catch { return NextResponse.json({ status: "error", message: "Database connection failed" }, { status: 503 }); }
}
