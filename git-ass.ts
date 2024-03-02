#!/usr/bin/env -S deno run -qA

import { cac } from "https://esm.sh/cac@6.7.14";
import { runCommand } from "https://raw.githubusercontent.com/gera2ld/deno-lib/main/lib/cli.ts";

const cli = cac("git-ass");
cli.help();
cli.command("").action(showHelpAndThrow);

// Unknown command
cli.on("command:*", showHelpAndThrow);

cli.command("prune", "Prune branches deleted on remote").action(async () => {
  await runCommand("git", {
    args: ["fetch", "--all", "--prune"],
  }).spawn();
});

cli.command("purge", "Remove fully merged local branches").action(async () => {
  const { branches, current } = await readBranches();
  for (const branch of branches) {
    if (branch === current) continue;
    const { success, stderr } = await runCommand("git", {
      args: ["branch", "-d", branch],
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

cli.parse();

function showHelpAndThrow() {
  cli.outputHelp();
  Deno.exit(1);
}

async function readBranches(remote = false) {
  const { stdout } = await runCommand("git", {
    args: ["branch", ...(remote ? ["-r"] : [])],
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
