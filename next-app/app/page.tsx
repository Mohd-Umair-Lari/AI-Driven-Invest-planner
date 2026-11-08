import { redirect } from "next/navigation";

export default function Home() {
  redirect("/static-pages/index.html");
}
