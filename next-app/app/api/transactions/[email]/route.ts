import { NextResponse } from "next/server";
import { getDb } from "@/lib/mongo";
import { authorizedEmail, matchesEmail } from "@/lib/request-auth";

type Context = { params: Promise<{ email: string }> };

export async function GET(_: Request, { params }: Context) {
  const email = decodeURIComponent((await params).email); const user = await (await getDb()).collection("userGoals").findOne({ email }, { projection: { transactions: 1 } });
  if (!user) return NextResponse.json({ detail: "User not found" }, { status: 404 });
  return NextResponse.json({ transactions: user.transactions ?? [] });
}

export async function POST(request: Request, { params }: Context) {
  const email = decodeURIComponent((await params).email); const transactions = await request.json();
  const authenticated = await authorizedEmail(request);
  if (authenticated instanceof Response) return authenticated;
  if (!matchesEmail(authenticated, email)) return NextResponse.json({ detail: "Forbidden" }, { status: 403 });
  if (!Array.isArray(transactions) || !transactions.length) return NextResponse.json({ detail: "No transactions provided" }, { status: 400 });
  const result = await (await getDb()).collection<any>("userGoals").updateOne({ email }, { $push: { transactions: { $each: transactions } } });
  if (!result.matchedCount) return NextResponse.json({ detail: "User not found" }, { status: 404 });
  return NextResponse.json({ status: "success", added: transactions.length }, { status: 201 });
}
