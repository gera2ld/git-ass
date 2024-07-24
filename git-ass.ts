#!/usr/bin/env -S deno run -qA

import { program } from "npm:commander@^12.0.0";
import { runCommand } from "https://raw.githubusercontent.com/gera2ld/deno-lib/main/lib/cli.ts";

program.name("git-ass");

program.command("prune")
  .description("Prune branches deleted on remote").action(async () => {
    await runCommand(["git", "fetch", "--all", "--prune"]).spawn();
  });

program.command("purge")
  .description("Remove fully merged local branches").action(async () => {
    const { branches, current } = await readBranches();
    for (const branch of branches) {
      if (branch === current) continue;
      const { success, stderr } = await runCommand([
        "git",
        "branch",
        "-d",
        branch,
      ], {
        stdout: "piped",
        stderr: "piped",
      }).output(false);
      let result = "ok";
      if (!success) {
        result = stderr.includes(" is not fully merged.")
          ? "not fully merged, skipping"
          : `error: ${stderr}`;
      }
      console.log(`- ${branch} - ${result}`);
    }
  });

program.parse();

async function readBranches(remote = false) {
  const { stdout } = await runCommand([
    "git",
    "branch",
    ...(remote ? ["-r"] : []),
  ], {
    stdout: "piped",
  }).output();
  const lines = stdout.split("\n");
  const current = lines
    .find((line) => line.startsWith("* "))
    ?.slice(2)
    .trim();
  const branches = lines.map((line) => line.slice(2).trim()).filter(Boolean);
  return { branches, current };
}
