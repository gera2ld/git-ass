#!/usr/bin/env -S deno run -qA

import { program } from "npm:commander@^12.0.0";
import { runCommand } from "https://gitlab.com/gera2ld/deno-lib/-/raw/main/lib/cli.ts";

program.name("git-ass");

program
  .command("prune")
  .description("Prune branches deleted on remote")
  .action(async () => {
    await runCommand(["git", "fetch", "--all", "--prune"]);
  });

program
  .command("purge")
  .description("Remove fully merged local branches")
  .action(async () => {
    const { branches, current } = await readBranches();
    for (const branch of branches) {
      if (branch === current) continue;
      const result = await runCommand(
        ["git", "branch", "-d", branch],
        {},
        {
          ensureSuccess: false,
          buffer: true,
        },
      );
      let output = "";
      if (!result.success) {
        const stderr = new TextDecoder().decode(await result.stderr());
        output = stderr.includes(" is not fully merged.")
          ? "not fully merged, skipping"
          : `error: ${stderr}`;
      }
      console.log(`- ${branch} - ${output}`);
    }
  });

program.parse();

async function readBranches(remote = false) {
  const result = await runCommand(
    ["git", "branch", ...(remote ? ["-r"] : [])],
    {},
    {
      buffer: true,
    },
  );
  const stdout = new TextDecoder().decode(await result.stdout());
  const lines = stdout.split("\n");
  const current = lines
    .find((line) => line.startsWith("* "))
    ?.slice(2)
    .trim();
  const branches = lines.map((line) => line.slice(2).trim()).filter(Boolean);
  return { branches, current };
}
