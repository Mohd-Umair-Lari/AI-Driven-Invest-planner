import { NextResponse } from "next/server";
import { getDb, stripMongoId } from "@/lib/mongo";
import { authorizedEmail, matchesEmail } from "@/lib/request-auth";

type Context = { params: Promise<{ email: string }> };

export async function GET(_: Request, { params }: Context) {
  const email = decodeURIComponent((await params).email);
  const user = await (await getDb()).collection("userGoals").findOne({ email }, { projection: { password: 0 } });
  if (!user) return NextResponse.json({ detail: "User not found" }, { status: 404 });
  return NextResponse.json({ status: "success", user: stripMongoId(user) });
}

export async function PUT(request: Request, { params }: Context) {
  const email = decodeURIComponent((await params).email); const body = await request.json();
  const authenticated = await authorizedEmail(request);
  if (authenticated instanceof Response) return authenticated;
  if (!matchesEmail(authenticated, email)) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  const db = await getDb(); const users = db.collection("userGoals"); const user = await users.findOne({ email });
  if (!user) return NextResponse.json({ detail: "User not found" }, { status: 404 });
  const update = {
    Name: body.Name ?? "", Age: String(body.Age ?? ""), "employment-status": body["employment-status"] ?? "",
    Goal: body.Goal ?? {}, financials: { ...(user.financials ?? {}), ...(body.financials ?? {}) },
    investments: { ...(user.investments ?? {}), ...(body.investments ?? {}) }, progress: { ...(user.progress ?? {}), ...(body.progress ?? {}) },
  };
  await users.updateOne({ email }, { $set: update });
  return NextResponse.json({ status: "success" });
}
