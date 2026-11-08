import { NextResponse } from "next/server";
import { authorizedEmail } from "@/lib/request-auth";
import { getDb, stripMongoId } from "@/lib/mongo";
export async function GET(request: Request) {
  const email = await authorizedEmail(request); if (email instanceof Response) return email;
  const user = await (await getDb()).collection<any>("userGoals").findOne({ email });
  if (!user) return NextResponse.json({ detail: "User not found" }, { status: 404 });
  return NextResponse.json({ status: "success", user: stripMongoId(user) });
}
