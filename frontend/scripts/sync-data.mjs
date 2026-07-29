import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";

const source = resolve("../data/sample/occupation_metrics.csv");
const destination = resolve("public/data/occupation_metrics.csv");

await mkdir(dirname(destination), { recursive: true });
await copyFile(source, destination);
