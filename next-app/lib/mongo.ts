import { MongoClient, type Db } from "mongodb";
import { env, requireEnv } from "./env";

const globalForMongo = globalThis as unknown as { mongoClientPromise?: Promise<MongoClient> };

function getClientPromise() {
  if (!globalForMongo.mongoClientPromise) {
    globalForMongo.mongoClientPromise = new MongoClient(requireEnv(env.mongoUri, "MONGO_URI")).connect();
  }
  return globalForMongo.mongoClientPromise;
}

export async function getDb(): Promise<Db> {
  return (await getClientPromise()).db(env.dbName);
}

export function stripMongoId<T extends Record<string, unknown>>(doc: T | null): T | null {
  if (!doc) return null;
  const { _id, password, ...safe } = doc;
  return { ...safe, ...(_id ? { id: String(_id) } : {}) } as T;
}
